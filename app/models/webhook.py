import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class WebhookDeliveryBase(BaseModel):
    subscription_id: uuid.UUID = Field(..., description="The subscription this delivery belongs to.")
    payload: Dict[str, Any] = Field(..., description="The JSON payload received.")

class WebhookDeliveryCreate(WebhookDeliveryBase):
    status: str = Field("pending", description="Initial status of the delivery.")

class WebhookDelivery(WebhookDeliveryBase):
    id: uuid.UUID = Field(..., description="Unique identifier for the delivery task.")
    status: str = Field(..., description="Current status (pending, processing, success, failed_attempt, failed).")
    created_at: datetime = Field(..., description="Timestamp when the webhook was ingested.")
    last_attempt_at: Optional[datetime] = Field(None, description="Timestamp of the last delivery attempt.")

    class Config:
        orm_mode = True 