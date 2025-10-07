# Phase 2: Email Integration & Data Pipeline

**Timeline**: Week 2

## Objectives

- Implement Gmail OAuth authentication flow
- Create email fetching service
- Build email parsing and normalization logic
- Setup background worker for email processing
- Implement email synchronization pipeline

## 2.1 Gmail OAuth Integration

### Email Service

```python
# backend/app/services/email_service.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64

class EmailService:
    def __init__(self, user_credentials: dict):
        self.credentials = Credentials(**user_credentials)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    async def fetch_emails(self, max_results: int = 50) -> list:
        """Fetch recent emails from Gmail"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                emails.append(self._parse_email(email_data))

            return emails
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")

    def _parse_email(self, email_data: dict) -> dict:
        """Parse Gmail API response into structured format"""
        headers = {h['name']: h['value']
                  for h in email_data['payload']['headers']}

        # Extract body
        body = ""
        if 'parts' in email_data['payload']:
            for part in email_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    break
        else:
            body = base64.urlsafe_b64decode(
                email_data['payload']['body']['data']
            ).decode('utf-8')

        return {
            'message_id': email_data['id'],
            'subject': headers.get('Subject', ''),
            'sender_email': headers.get('From', ''),
            'received_at': headers.get('Date', ''),
            'body_text': body,
            'snippet': email_data.get('snippet', '')
        }
```

## 2.2 Email Processing Worker

### Background Task Processor

```python
# backend/app/workers/email_processor.py
from celery import Celery
from app.services.triage_service import TriageService
from app.models.email import Email
from app.core.database import SessionLocal

celery_app = Celery('email_processor')

@celery_app.task
def process_email(email_id: str):
    """Background task to process and classify email"""
    db = SessionLocal()

    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return {'error': 'Email not found'}

        triage_service = TriageService()

        # Classify email
        classification = triage_service.classify_email(
            subject=email.subject,
            body=email.body_text,
            sender=email.sender_email
        )

        # Update email with classification
        email.category = classification['category']
        email.priority = classification['priority']
        email.urgency_score = classification['urgency_score']
        email.sentiment = classification['sentiment']
        email.requires_action = classification['requires_action']

        db.commit()

        return {'status': 'processed', 'email_id': email_id}

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

## 2.3 OAuth Flow Implementation

### Authentication Endpoints

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from google_auth_oauthlib.flow import Flow
from app.core.config import settings

router = APIRouter()

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    return {'authorization_url': authorization_url, 'state': state}

@router.get("/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth callback"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        state=state
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Store credentials in database
    # ... (user creation/update logic)

    return {'status': 'authenticated'}
```

## 2.4 Email Sync Worker

### Periodic Email Fetching

```python
# backend/app/workers/sync_worker.py
from celery import Celery
from app.services.email_service import EmailService
from app.models.email import Email
from app.core.database import SessionLocal

celery_app = Celery('sync_worker')

@celery_app.task
def fetch_new_emails(user_id: str):
    """Fetch new emails for a user"""
    db = SessionLocal()

    try:
        # Get user credentials
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {'error': 'User not found'}

        # Initialize email service
        email_service = EmailService({
            'token': user.access_token,
            'refresh_token': user.refresh_token,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET
        })

        # Fetch emails
        emails = await email_service.fetch_emails(max_results=50)

        # Store emails in database
        new_emails = 0
        for email_data in emails:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.message_id == email_data['message_id']
            ).first()

            if not existing:
                email = Email(
                    user_id=user_id,
                    message_id=email_data['message_id'],
                    subject=email_data['subject'],
                    sender_email=email_data['sender_email'],
                    body_text=email_data['body_text'],
                    received_at=email_data['received_at']
                )
                db.add(email)
                new_emails += 1

                # Queue for processing
                process_email.delay(str(email.id))

        db.commit()

        return {'status': 'success', 'new_emails': new_emails}

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

## 2.5 Email Models

### SQLAlchemy Models

```python
# backend/app/models/email.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    message_id = Column(String(255), unique=True, nullable=False)
    subject = Column(Text)
    sender_email = Column(String(255))
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
    created_at = Column(DateTime, server_default='now()')

    # Relationships
    user = relationship("User", back_populates="emails")
    classifications = relationship("EmailClassification", back_populates="email")
    responses = relationship("GeneratedResponse", back_populates="email")
```

## Deliverables

- ✅ Gmail OAuth authentication flow
- ✅ Email fetching service with API integration
- ✅ Email parsing and normalization
- ✅ Background worker for email processing
- ✅ Periodic sync mechanism
- ✅ Email storage in PostgreSQL
- ✅ Error handling and retry logic
- ✅ Credential management and token refresh

## Success Criteria

- Successfully authenticate with Gmail
- Fetch emails from inbox
- Parse email data correctly
- Store emails in database without duplicates
- Background processing queue working
- Handle API rate limits gracefully
- Automatic token refresh on expiry
