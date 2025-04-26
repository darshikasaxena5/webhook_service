import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.db.client import get_db
from app.db import deliveries as db_deliveries
from app.db import attempts as db_attempts
from app.db import stats as db_stats # Import the new stats db functions
from app.db import activity as db_activity # Import activity db functions
from app.models.status import DeliveryStatus, SystemStats # Import new model
from app.models.attempt import DeliveryAttempt # Response model for list of attempts
from app.models.activity import ActivityItem # Import activity model

router = APIRouter()

@router.get(
    "/deliveries/{delivery_id}/status", 
    response_model=DeliveryStatus,
    summary="Get status and attempt history for a delivery task",
    tags=["Status & Analytics"]
)
def get_delivery_status_and_attempts(
    delivery_id: uuid.UUID,
    db: Client = Depends(get_db)
):
    """Retrieve the current status and full attempt history for a specific delivery task ID."""
    delivery = db_deliveries.get_delivery(db=db, delivery_id=delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Delivery task with ID {delivery_id} not found."
        )
        
    attempts = db_attempts.get_attempts_for_delivery(db=db, delivery_id=delivery_id)
    
    return DeliveryStatus(delivery=delivery, attempts=attempts)

@router.get(
    "/subscriptions/{subscription_id}/attempts",
    response_model=List[DeliveryAttempt],
    summary="List recent delivery attempts for a subscription",
    tags=["Status & Analytics"]
)
def list_recent_attempts_for_subscription(
    subscription_id: uuid.UUID,
    limit: int = 20, # Default limit, can be adjusted via query parameter
    db: Client = Depends(get_db)
):
    """Retrieve the most recent delivery attempts (across all deliveries) for a specific subscription ID."""
    # Note: The underlying DB function `get_recent_attempts_for_subscription` currently uses a
    # potentially less efficient N+1 query approach. Consider optimizing with RPC if needed.
    attempts = db_attempts.get_recent_attempts_for_subscription(
        db=db, 
        subscription_id=subscription_id, 
        limit=limit
    )
    # No need to check if subscription exists here, the DB function handles empty results.
    return attempts 

# --- New Endpoint for System Stats --- 
@router.get(
    "/stats", 
    response_model=SystemStats,
    summary="Get dashboard statistics",
    tags=["Status & Analytics"]
)
async def get_dashboard_stats(db: Client = Depends(get_db)):
    """Retrieve aggregated statistics for the system dashboard.
    
    - **total_subscriptions**: Count of all active subscriptions.
    - **recent_success_count**: Deliveries marked 'success' in the last 24 hours.
    - **recent_failed_count**: Deliveries marked 'failed' (permanently) in the last 24 hours.
    """
    # The db function already handles potential errors and raises HTTPException
    stats_data = await db_stats.get_system_stats(db=db)
    return SystemStats(**stats_data) 

# --- New Endpoint for Recent Activity --- 
@router.get(
    "/activity",
    response_model=List[ActivityItem],
    summary="Get recent system activity feed",
    tags=["Status & Analytics"]
)
async def get_recent_activity_feed(
    limit: int = Query(5, ge=1, le=20, description="Number of activity items to return"),
    db: Client = Depends(get_db)
):
    """Retrieve a list of the most recent activities across the system,
    such as subscription creations and delivery attempts.
    """
    # db function returns empty list on error, safe to return directly
    activity_data = await db_activity.get_recent_activity(db=db, limit=limit)
    # Pydantic will validate the list items against ActivityItem model
    return activity_data 