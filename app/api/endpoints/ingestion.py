import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from supabase import Client
import json
import time  # Import time module

from app.db.client import get_db
from app.db import subscriptions as db_subscriptions
from app.db import deliveries as db_deliveries
from app.tasks.delivery import deliver_webhook
from app.core.security import verify_signature

router = APIRouter()

# Define the signature header name
SIGNATURE_HEADER = "X-Webhook-Signature-256"

@router.post(
    "/{subscription_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a webhook payload for a subscription",
    tags=["Ingestion"],
)
async def ingest_webhook(
    subscription_id: uuid.UUID,
    request: Request,
    db: Client = Depends(get_db)
):
    """
    Accepts incoming webhook payloads (JSON), verifies signature (if secret exists),
    and queues them for delivery.
    
    - Validates the subscription ID.
    - Reads raw request body.
    - Verifies signature using X-Webhook-Signature-256 header if secret is set.
    - Parses JSON payload.
    - Stores the payload and creates a delivery task record.
    - Enqueues a background task for asynchronous delivery.
    - Returns 202 Accepted on success, 401/400 on verification failure.
    """
    # 1. Validate Subscription ID & Get Secret
    subscription = db_subscriptions.get_subscription(db=db, subscription_id=subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found."
        )
    
    # 2. Read Raw Body for Signature Verification
    raw_body: bytes = await request.body()

    # 3. Verify Signature (if secret key is present)
    signature_header = request.headers.get(SIGNATURE_HEADER)
    if not verify_signature(secret=subscription.secret_key, request_body=raw_body, signature_header=signature_header):
        # Signature is required and invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 400 Bad Request
            detail="Invalid webhook signature."
        )

    # 4. Parse JSON Payload (only after verifying signature on raw body)
    try:
        # We need to parse the raw body now, as request.json() consumes the stream
        payload: Dict[str, Any] = {} 
        if raw_body:
            payload = json.loads(raw_body.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {e}"
        )
    except Exception as e:
        # Catch potential decoding errors or other issues
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing payload: {e}"
        )

    # 5. Create Webhook Delivery Record in DB
    start_db_time = time.time()
    print(f"[Ingest {subscription_id}] Creating DB record...")
    delivery_record = db_deliveries.create_webhook_delivery(
        db=db,
        subscription_id=subscription_id,
        payload=payload
    )
    db_duration = time.time() - start_db_time
    print(f"[Ingest {subscription_id}] DB record created (took {db_duration:.4f}s). ID: {delivery_record.id if delivery_record else 'Failed'}")

    if not delivery_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook delivery record."
        )

    # 6. Enqueue Celery Task
    start_celery_time = time.time()
    delivery_id_str = str(delivery_record.id)
    print(f"[Ingest {subscription_id}] Enqueuing Celery task for delivery ID: {delivery_id_str}...")
    try:
        deliver_webhook.delay(delivery_id_str)
        celery_duration = time.time() - start_celery_time
        print(f"[Ingest {subscription_id}] Celery task enqueued (took {celery_duration:.4f}s).")
    except Exception as e:
        celery_duration = time.time() - start_celery_time
        print(f"[Ingest {subscription_id}] Celery task enqueue FAILED after {celery_duration:.4f}s: {e}")
        # Optional: Decide if you want to raise an error here or just log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue webhook task: {e}"
        )

    # 7. Return 202 Accepted
    print(f"[Ingest {subscription_id}] Request finished, returning 202.")
    return
