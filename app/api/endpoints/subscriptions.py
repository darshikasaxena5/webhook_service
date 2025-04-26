import uuid
from typing import List
import redis # Import redis
from fastapi import APIRouter, Depends, HTTPException, status, Query # Added Query
from supabase import Client

from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate, PaginatedSubscriptions # Added Paginated model
from app.db.client import get_db
from app.core.cache import get_cache, delete_subscription_from_cache # Import cache dependency and delete function
from app.db import subscriptions as db_subscriptions # Use alias to avoid name clashes

router = APIRouter()

@router.post(
    "/",
    response_model=Subscription,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new webhook subscription",
    tags=["Subscriptions"]
)
def create_new_subscription(
    subscription_in: SubscriptionCreate,
    db: Client = Depends(get_db)
):
    """Register a new target URL to receive webhooks."""
    created_subscription = db_subscriptions.create_subscription(db=db, subscription=subscription_in)
    if not created_subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create subscription."
        )
    return created_subscription

@router.get(
    "/",
    response_model=PaginatedSubscriptions, # Use the new paginated model
    summary="List all webhook subscriptions (paginated)",
    tags=["Subscriptions"]
)
async def list_all_subscriptions(
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    limit: int = Query(10, ge=1, le=100, description="Number of subscriptions per page"),
    db: Client = Depends(get_db)
):
    """Retrieve a paginated list of all active subscriptions."""
    offset = (page - 1) * limit
    subscriptions_list, total_count = await db_subscriptions.get_subscriptions(
        db=db, 
        offset=offset, 
        limit=limit
    )
    # The db function already converts to Subscription models
    return PaginatedSubscriptions(total_count=total_count, subscriptions=subscriptions_list)

@router.get(
    "/{subscription_id}",
    response_model=Subscription,
    summary="Get a specific subscription by ID",
    tags=["Subscriptions"]
)
def get_single_subscription(
    subscription_id: uuid.UUID,
    db: Client = Depends(get_db)
):
    """Retrieve details for a specific subscription."""
    subscription = db_subscriptions.get_subscription(db=db, subscription_id=subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found."
        )
    return subscription

@router.put(
    "/{subscription_id}",
    response_model=Subscription,
    summary="Update a subscription",
    tags=["Subscriptions"]
)
def update_existing_subscription(
    subscription_id: uuid.UUID,
    subscription_update: SubscriptionUpdate,
    db: Client = Depends(get_db),
    cache: redis.Redis = Depends(get_cache) # Inject cache client
):
    """Update the target URL or secret key for a subscription."""
    # First, check if it exists
    existing_subscription = db_subscriptions.get_subscription(db=db, subscription_id=subscription_id)
    if existing_subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found."
        )
    
    updated_subscription = db_subscriptions.update_subscription(
        db=db, 
        subscription_id=subscription_id, 
        subscription_update=subscription_update
    )
    if updated_subscription is None:
         # Update itself failed (potentially) - though update_subscription handles internal errors
         # Or it might return None if the row wasn't found after check (race condition? unlikely)
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if we suspect it vanished
            detail=f"Could not update subscription {subscription_id}."
         )
         
    # Invalidate cache
    if cache:
        delete_subscription_from_cache(cache, subscription_id)
        
    return updated_subscription

@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a subscription",
    tags=["Subscriptions"]
)
def delete_existing_subscription(
    subscription_id: uuid.UUID,
    db: Client = Depends(get_db),
    cache: redis.Redis = Depends(get_cache) # Inject cache client
):
    """Remove a webhook subscription."""
    deleted = db_subscriptions.delete_subscription(db=db, subscription_id=subscription_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found or could not be deleted."
        )
    # No content to return on successful delete
    
    # Invalidate cache
    if cache:
        delete_subscription_from_cache(cache, subscription_id)
        
    return None 