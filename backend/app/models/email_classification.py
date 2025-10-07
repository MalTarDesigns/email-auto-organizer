from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class EmailClassification(Base):
    __tablename__ = "email_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(UUID(as_uuid=True), ForeignKey('emails.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    urgency_score = Column(Numeric(3, 2))
    sentiment = Column(String(20))
    confidence_score = Column(Numeric(3, 2))
    reasoning = Column(Text)
    metadata = Column(JSON)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="classifications")
