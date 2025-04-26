import uuid
import httpx
import os
import json
from datetime import datetime, timezone
from app.tasks.celery_app import celery_app
from app.db.client import get_db # Import the dependency function
from app.core.cache import get_cache, get_subscription_from_cache, set_subscription_in_cache # Import cache functions
from app.db import deliveries as db_deliveries
from app.db import subscriptions as db_subscriptions
from app.db import attempts as db_attempts
from app.models.attempt import DeliveryAttemptCreate
from celery.exceptions import MaxRetriesExceededError

# Load settings from environment variables
# Provide defaults matching the requirements
MAX_RETRIES = int(os.environ.get("WEBHOOK_MAX_RETRIES", 5))
# Exponential backoff starts at 10s: 10s, 30s, 1m, 5m, 15m (approx)
# Celery uses base 2 backoff: delay * 2 ** retry_count. We can adjust base or start delay.
# Let's use a base delay and let Celery handle the exponential part.
INITIAL_RETRY_DELAY_SECONDS = 10 # Corresponds to retry_backoff param
# Max backoff time (e.g., 15 minutes = 900 seconds)
MAX_RETRY_BACKOFF_SECONDS = 900
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", 10))

class DeliveryFailureError(Exception):
    "Custom exception for non-2xx responses to trigger retries."
    def __init__(self, status_code: int, response_body: str):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"Delivery failed with status {status_code}")

# Configure the Celery task with automatic retries
@celery_app.task(
    bind=True, 
    autoretry_for=(httpx.RequestError, httpx.TimeoutException, DeliveryFailureError), # Retry on network errors, timeouts, and non-2xx status
    retry_kwargs={'max_retries': MAX_RETRIES},
    retry_backoff=INITIAL_RETRY_DELAY_SECONDS, # Use this as base delay for exponential backoff
    retry_backoff_max=MAX_RETRY_BACKOFF_SECONDS,
    retry_jitter=True # Add randomness to avoid thundering herd
)
def deliver_webhook(self, delivery_id_str: str):
    """
    Celery task to attempt webhook delivery with retries.
    """
    delivery_id = uuid.UUID(delivery_id_str)
    db = get_db() # Get a Supabase client instance
    cache = get_cache() # Get cache client instance
    attempt_number = self.request.retries + 1
    print(f"[Attempt {attempt_number}/{MAX_RETRIES + 1}] Processing delivery: {delivery_id}")

    # --- Fetch Data --- 
    delivery = db_deliveries.get_delivery(db, delivery_id)
    if not delivery:
        print(f"[Error] Delivery task {delivery_id} not found in DB. Stopping.")
        return # Or raise Ignore() if preferred
        
    # Check if already succeeded or failed permanently
    if delivery.status in ["success", "failed"]:
         print(f"[Info] Delivery {delivery_id} already in terminal state '{delivery.status}'. Skipping.")
         return

    # --- Fetch Subscription Data (with Cache) --- 
    subscription = None
    if cache: # Check if cache connection is available
        subscription = get_subscription_from_cache(cache, delivery.subscription_id)
    
    if not subscription: # Cache miss or cache unavailable
        subscription = db_subscriptions.get_subscription(db, delivery.subscription_id)
        if subscription and cache: # If fetched from DB and cache is available, store it
            set_subscription_in_cache(cache, subscription)

    if not subscription:
        print(f"[Error] Subscription {delivery.subscription_id} not found (DB & Cache) for delivery {delivery_id}. Marking as failed.")
        db_deliveries.update_delivery_status(db, delivery_id, status="failed", last_attempt_at=datetime.now(timezone.utc))
        return

    # --- Update Status to Processing --- 
    if delivery.status != "processing": # Only update if not already processing (e.g., on retry)
        db_deliveries.update_delivery_status(db, delivery_id, status="processing")

    # --- Attempt Delivery --- 
    target_url = str(subscription.target_url)
    payload = delivery.payload # This should be a dict/list already from JSONB
    headers = {'Content-Type': 'application/json'}
    # TODO: Add signature header if secret_key exists (Bonus)

    status_code = None
    response_body = None
    error_message = None
    outcome = "failed" # Assume failure unless proven otherwise
    now = datetime.now(timezone.utc)

    try:
        # Using httpx for async requests if needed, but sync is fine in Celery task
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(target_url, json=payload, headers=headers)
            
        status_code = response.status_code
        # Read response body carefully - potentially large
        # Limit stored body size if necessary (e.g., first 1KB)
        response_body = response.text # Or response.read() for bytes, limit size here
        
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx
        
        # --- Success --- 
        outcome = "success"
        print(f"[Success] Delivery {delivery_id} successful to {target_url} (Status: {status_code})")
        db_deliveries.update_delivery_status(db, delivery_id, status="success", last_attempt_at=now)

    except httpx.TimeoutException as e:
        error_message = f"Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds."
        print(f"[Failure] Delivery {delivery_id} to {target_url}: {error_message}")
        # Let autoretry_for handle the retry by re-raising
        raise e 
    except httpx.RequestError as e: # Covers connection errors, DNS errors, etc.
        error_message = f"Request failed: {type(e).__name__} - {e}"
        print(f"[Failure] Delivery {delivery_id} to {target_url}: {error_message}")
        # Let autoretry_for handle the retry by re-raising
        raise e 
    except httpx.HTTPStatusError as e: # Catches non-2xx responses from raise_for_status()
        error_message = f"Target returned non-2xx status: {e.response.status_code}"
        print(f"[Failure] Delivery {delivery_id} to {target_url}: {error_message}")
        # Wrap in custom error to trigger retry based on non-2xx status
        raise DeliveryFailureError(status_code=e.response.status_code, response_body=response_body) from e
    except Exception as e:
        # Catch any other unexpected errors during processing
        error_message = f"Unexpected error: {type(e).__name__} - {e}"
        print(f"[Failure] Delivery {delivery_id} to {target_url}: {error_message}")
        # Update status to failed_attempt here, but decide if retryable
        # For unexpected errors, maybe don't retry automatically? Or configure separately.
        # For now, we let the current retry logic handle it if it was configured, otherwise it stops.
        # Let's explicitly raise to ensure retry logic catches it if configured, otherwise fails task
        raise e
    finally:
        # --- Log Attempt --- 
        attempt_log = DeliveryAttemptCreate(
            delivery_id=delivery_id,
            attempt_number=attempt_number,
            outcome=outcome,
            status_code=status_code,
            response_body=response_body, # Consider truncating
            error_message=error_message
        )
        db_attempts.create_delivery_attempt(db, attempt_log)

        # --- Update Status on Failure (if not success) --- 
        if outcome == "failed":
            # Check if max retries have been reached
            if self.request.retries >= MAX_RETRIES:
                print(f"[Failed Permanently] Delivery {delivery_id} failed after {MAX_RETRIES + 1} attempts.")
                db_deliveries.update_delivery_status(db, delivery_id, status="failed", last_attempt_at=now)
            else:
                # Mark as failed attempt, will be retried by Celery
                print(f"[Failed Attempt] Delivery {delivery_id} attempt {attempt_number} failed. Will retry.")
                db_deliveries.update_delivery_status(db, delivery_id, status="failed_attempt", last_attempt_at=now)

    return f"Delivery {delivery_id} attempt {attempt_number} resulted in {outcome}"

# Optional: Add specific error handling for MaxRetriesExceededError if needed
# This can be done via try...except around the self.retry() call if manual retry is used,
# or potentially via Celery's signals or task failure handlers if using autoretry.
# For autoretry, the task just fails after max retries. We handle the final 'failed' status update
# within the main task logic (in the finally block). 