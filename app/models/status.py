from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.webhook import WebhookDelivery
from app.models.attempt import DeliveryAttempt
import uuid
from datetime import datetime

class DeliveryStatus(BaseModel):
    """Response model for getting status and attempts for a single delivery."""
    delivery: WebhookDelivery = Field(..., description="The details of the webhook delivery task.")
    attempts: List[DeliveryAttempt] = Field(..., description="A list of all delivery attempts made for this task.")

    class Config:
        orm_mode = True

# --- New Model for Dashboard Stats ---
class SystemStats(BaseModel):
    """Statistics for the system dashboard."""
    total_subscriptions: int = Field(..., description="Total number of active subscriptions")
    recent_success_count: int = Field(..., description="Number of successful deliveries in the recent period (e.g., 24h)")
    recent_failed_count: int = Field(..., description="Number of permanently failed deliveries in the recent period (e.g., 24h)")
    # Add other stats as needed

    class Config:
        # Example for Pydantic v1 if needed
        # orm_mode = True
        # If using Pydantic v2, configuration might differ slightly or not be needed
        # for basic models like this. 
        pass 