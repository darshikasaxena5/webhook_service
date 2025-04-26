import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DeliveryAttemptBase(BaseModel):
    delivery_id: uuid.UUID = Field(..., description="The delivery task this attempt belongs to.")
    attempt_number: int = Field(..., gt=0, description="The attempt number (1 for initial, 2+ for retries).")
    outcome: str = Field(..., description="Outcome of the attempt (e.g., 'success', 'failed').")
    status_code: Optional[int] = Field(None, description="HTTP status code received from the target.")
    response_body: Optional[str] = Field(None, description="Response body from the target URL (truncated if necessary).")
    error_message: Optional[str] = Field(None, description="Details of the error if the attempt failed.")

class DeliveryAttemptCreate(DeliveryAttemptBase):
    # Timestamp is set by default in DB
    pass

class DeliveryAttempt(DeliveryAttemptBase):
    id: int = Field(..., description="Unique identifier for the delivery attempt log entry.")
    timestamp: datetime = Field(..., description="Timestamp when the attempt was made.")

    class Config:
        orm_mode = True 