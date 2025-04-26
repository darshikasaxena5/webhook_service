import uuid
from typing import List, Optional, Tuple
from supabase import Client
from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate
from app.db.client import get_db # Reuse the client
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Table name constant
TABLE_NAME = "subscriptions"

def create_subscription(db: Client, subscription: SubscriptionCreate) -> Optional[Subscription]:
    """Creates a new subscription record in the database."""
    try:
        # Convert HttpUrl to string before inserting
        insert_data = subscription.dict(exclude_unset=True)
        if 'target_url' in insert_data:
            insert_data['target_url'] = str(insert_data['target_url'])
            
        response = db.table(TABLE_NAME)\
                     .insert(insert_data)\
                     .execute()
        if response.data:
            return Subscription(**response.data[0])
    except Exception as e:
        print(f"Error creating subscription: {e}") # Basic error logging
    return None

def get_subscription(db: Client, subscription_id: uuid.UUID) -> Optional[Subscription]:
    """Retrieves a specific subscription by its ID."""
    try:
        response = db.table(TABLE_NAME)\
                     .select("*")\
                     .eq("id", str(subscription_id))\
                     .limit(1)\
                     .execute()
        if response.data:
            return Subscription(**response.data[0])
    except Exception as e:
        print(f"Error getting subscription {subscription_id}: {e}")
    return None

async def get_subscriptions(db: Client, offset: int = 0, limit: int = 10) -> Tuple[List[Subscription], int]:
    """Retrieves a list of subscriptions with pagination and total count."""
    try:
        # Execute the query with range for pagination and count for total
        response = db.table('subscriptions') \
            .select('*', count='exact') \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        subscriptions_data = response.data
        total_count = response.count
        
        # Convert dicts to Subscription models
        subscriptions = [Subscription(**item) for item in subscriptions_data]
        return subscriptions, total_count
        
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching subscriptions."
        )

def update_subscription(db: Client, subscription_id: uuid.UUID, subscription_update: SubscriptionUpdate) -> Optional[Subscription]:
    """Updates an existing subscription."""
    update_data = subscription_update.dict(exclude_unset=True)
    if not update_data:
        return get_subscription(db, subscription_id)
    
    # Convert HttpUrl to string if present
    if 'target_url' in update_data and update_data['target_url']:
         update_data['target_url'] = str(update_data['target_url'])
    
    if 'secret_key' in update_data and update_data['secret_key'] == '':
        update_data['secret_key'] = None

    try:
        response = db.table(TABLE_NAME)\
                     .update(update_data)\
                     .eq("id", str(subscription_id))\
                     .execute()
        if response.data:
            return Subscription(**response.data[0])
    except Exception as e:
        print(f"Error updating subscription {subscription_id}: {e}")
    return None

def delete_subscription(db: Client, subscription_id: uuid.UUID) -> bool:
    """Deletes a subscription by its ID."""
    try:
        response = db.table(TABLE_NAME)\
                     .delete()\
                     .eq("id", str(subscription_id))\
                     .execute()
        # Supabase delete often returns the deleted data, check if something was processed
        return bool(response.data)
    except Exception as e:
        print(f"Error deleting subscription {subscription_id}: {e}")
        return False 