import uuid
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List

class SubscriptionBase(BaseModel):
    target_url: HttpUrl = Field(..., description="The URL where the webhook payload should be delivered.")
    secret_key: Optional[str] = Field(None, description="Optional secret key for HMAC-SHA256 signature verification.")

class SubscriptionCreate(SubscriptionBase):
    pass # Inherits fields from SubscriptionBase

class SubscriptionUpdate(BaseModel):
    target_url: Optional[HttpUrl] = Field(None, description="New target URL.")
    secret_key: Optional[str] = Field(None, description="New secret key. Use null or omit to keep existing, or explicitly provide empty string to remove.")

class Subscription(SubscriptionBase):
    id: uuid.UUID = Field(..., description="Unique identifier for the subscription.")
    created_at: datetime = Field(..., description="Timestamp when the subscription was created.")
    updated_at: datetime = Field(..., description="Timestamp when the subscription was last updated.")

    class Config:
        from_attributes = True # Use Pydantic V2 config

class PaginatedSubscriptions(BaseModel):
    """Response model for paginated list of subscriptions."""
    total_count: int = Field(..., description="The total number of subscriptions available.")
    subscriptions: List[Subscription] = Field(..., description="The list of subscriptions for the current page.") 