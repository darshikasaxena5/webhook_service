from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class ActivityItem(BaseModel):
    """Represents a single item in the recent activity feed."""
    type: Literal['subscription_created', 'delivery_attempt'] = Field(..., description="Type of activity event")
    id: str = Field(..., description="Relevant ID (Subscription ID or Delivery Attempt ID)")
    timestamp: datetime = Field(..., description="Timestamp of the event")
    details: str = Field(..., description="A summary string describing the event")

    class Config:
        # orm_mode = True
        from_attributes = True # Use Pydantic V2 config 