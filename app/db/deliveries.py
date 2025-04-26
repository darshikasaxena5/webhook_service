import uuid
from typing import Optional, Dict, Any
from supabase import Client
from app.models.webhook import WebhookDelivery # Import the response model

# Table name constant
TABLE_NAME = "webhook_deliveries"

def create_webhook_delivery(db: Client, subscription_id: uuid.UUID, payload: Dict[str, Any]) -> Optional[WebhookDelivery]:
    """Creates a new webhook delivery record with 'pending' status."""
    try:
        # Prepare data consistent with WebhookDeliveryCreate internal structure
        delivery_data = {
            "subscription_id": str(subscription_id), # Ensure UUID is string for Supabase client
            "payload": payload,
            "status": "pending" # Default status
        }
        response = db.table(TABLE_NAME)\
                     .insert(delivery_data)\
                     .execute()
        if response.data:
            # Convert returned data back to the WebhookDelivery model
            return WebhookDelivery(**response.data[0])
    except Exception as e:
        print(f"Error creating webhook delivery for subscription {subscription_id}: {e}")
    return None

def get_delivery(db: Client, delivery_id: uuid.UUID) -> Optional[WebhookDelivery]:
    """Retrieves a specific webhook delivery task by its ID."""
    try:
        response = db.table(TABLE_NAME)\
                     .select("*")\
                     .eq("id", str(delivery_id))\
                     .limit(1)\
                     .execute()
        if response.data:
            return WebhookDelivery(**response.data[0])
    except Exception as e:
        print(f"Error getting delivery {delivery_id}: {e}")
    return None

def update_delivery_status(db: Client, delivery_id: uuid.UUID, status: str, last_attempt_at: Optional[Any] = None) -> Optional[WebhookDelivery]:
    """Updates the status and optionally the last_attempt_at timestamp of a delivery."""
    update_data = {"status": status}
    if last_attempt_at:
        # Ensure datetime is properly formatted if needed, though Supabase client might handle it
        update_data["last_attempt_at"] = last_attempt_at.isoformat()
        
    try:
        response = db.table(TABLE_NAME)\
                     .update(update_data)\
                     .eq("id", str(delivery_id))\
                     .execute()
        if response.data:
            return WebhookDelivery(**response.data[0])
    except Exception as e:
        print(f"Error updating delivery status for {delivery_id}: {e}")
    return None

# Add other DB functions for webhook_deliveries later (e.g., update status, get by ID) 