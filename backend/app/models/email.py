from sqlalchemy import Column, String, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    subject = Column(Text)
    sender_email = Column(String(255), index=True)
    sender_name = Column(String(255))
    body_text = Column(Text)
    body_html = Column(Text)
    received_at = Column(DateTime)
    processed_at = Column(DateTime)
    category = Column(String(50))
    priority = Column(String(20))
    urgency_score = Column(Numeric(3, 2))
    sentiment = Column(String(20))
    requires_action = Column(Boolean, default=False)
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small produces 1536 dimensions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emails")
    classifications = relationship("EmailClassification", back_populates="email", cascade="all, delete-orphan")
