from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


class EmailBase(BaseModel):
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class EmailCreate(EmailBase):
    message_id: str
    user_id: UUID
    received_at: Optional[datetime] = None


class EmailUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    urgency_score: Optional[Decimal] = None
    sentiment: Optional[str] = None
    requires_action: Optional[bool] = None
    processed_at: Optional[datetime] = None


class EmailInDB(EmailBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    message_id: str
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    urgency_score: Optional[Decimal] = None
    sentiment: Optional[str] = None
    requires_action: bool
    created_at: datetime
    updated_at: datetime


class Email(EmailInDB):
    pass


class EmailWithClassification(Email):
    classification: Optional[dict] = None
