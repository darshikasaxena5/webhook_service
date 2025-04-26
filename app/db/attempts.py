from supabase import Client
from app.models.attempt import DeliveryAttempt, DeliveryAttemptCreate
from typing import Optional, List
from datetime import datetime
import uuid

TABLE_NAME = "delivery_attempts"

def create_delivery_attempt(db: Client, attempt_log: DeliveryAttemptCreate) -> Optional[DeliveryAttempt]:
    """Logs a single delivery attempt to the database."""
    try:
        # Convert UUID to string before inserting
        insert_data = attempt_log.dict(exclude_unset=True)
        if 'delivery_id' in insert_data:
            insert_data['delivery_id'] = str(insert_data['delivery_id'])
            
        response = db.table(TABLE_NAME)\
                     .insert(insert_data)\
                     .execute()
        if response.data:
            return DeliveryAttempt(**response.data[0])
    except Exception as e:
        # Log the error but don't necessarily stop the main task if logging fails
        print(f"Error creating delivery attempt log for delivery {attempt_log.delivery_id}: {e}") 
    return None

def delete_attempts_older_than(db: Client, cutoff_time: datetime) -> int:
    """Deletes delivery attempt logs older than the specified cutoff time.
    
    Returns:
        The number of rows deleted, or -1 if an error occurred.
    """
    deleted_count = -1
    try:
        # Format timestamp for Supabase/Postgres query
        # Ensure it's timezone-aware if cutoff_time is timezone-aware
        cutoff_iso = cutoff_time.isoformat()

        response = db.table(TABLE_NAME)\
                     .delete()\
                     .lt("timestamp", cutoff_iso) \
                     .execute()
        
        # Supabase delete returns the deleted records in response.data
        deleted_count = len(response.data) if response.data else 0
        print(f"Deleted {deleted_count} delivery attempt logs older than {cutoff_iso}")
    except Exception as e:
        print(f"Error deleting old delivery attempt logs: {e}")
        # Return -1 or raise exception based on desired error handling
        return -1
    return deleted_count

def get_attempts_for_delivery(db: Client, delivery_id: uuid.UUID) -> List[DeliveryAttempt]:
    """Retrieves all delivery attempts for a specific delivery ID, ordered by attempt number."""
    try:
        response = db.table(TABLE_NAME)\
                     .select("*")\
                     .eq("delivery_id", str(delivery_id))\
                     .order("attempt_number", desc=False)\
                     .execute()
        if response.data:
            return [DeliveryAttempt(**item) for item in response.data]
    except Exception as e:
        print(f"Error getting attempts for delivery {delivery_id}: {e}")
    return []

def get_recent_attempts_for_subscription(db: Client, subscription_id: uuid.UUID, limit: int = 20) -> List[DeliveryAttempt]:
    """Retrieves the most recent delivery attempts across all deliveries for a specific subscription ID."""
    try:
        # This requires a join or a more complex query if we strictly filter by subscription_id *before* limiting.
        # A simpler approach (might be less efficient for huge logs) is to fetch recent logs and filter in code, 
        # or fetch logs for deliveries belonging to the subscription.
        # Let's try fetching recent attempts where the related delivery matches the subscription_id.
        # Note: Supabase Python client might not directly support joins like this easily.
        # Alternative: Query webhook_deliveries first, then query attempts.
        # Simpler/Less efficient: Fetch recent N attempts globally and filter? No, needs subscription filter.
        
        # Workaround: Fetch recent deliveries for the subscription, then their attempts (N+1 query potential)
        # OR, use Supabase RPC if join performance is critical.
        
        # Fetching attempts directly, ordered by time, requires joining/filtering on delivery's subscription_id.
        # Let's assume direct filtering isn't trivial. We'll retrieve deliveries first.
        
        # Query deliveries associated with the subscription first (adjust limit as needed)
        deliveries_response = db.table("webhook_deliveries")\
                                .select("id")\
                                .eq("subscription_id", str(subscription_id))\
                                .order("created_at", desc=True)\
                                .limit(limit * 2) \
                                .execute()
                                
        if not deliveries_response.data:
            return []
            
        delivery_ids = [item['id'] for item in deliveries_response.data]

        # Now fetch attempts for these delivery IDs
        response = db.table(TABLE_NAME)\
                     .select("*")\
                     .in_("delivery_id", delivery_ids)\
                     .order("timestamp", desc=True)\
                     .limit(limit)\
                     .execute()

        if response.data:
            return [DeliveryAttempt(**item) for item in response.data]
            
    except Exception as e:
        print(f"Error getting recent attempts for subscription {subscription_id}: {e}")
    return []

# Add functions to retrieve attempts later (Step 7)