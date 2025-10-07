# Phase 6: API Endpoints

**Timeline**: Week 6

## Objectives

- Implement comprehensive REST API
- Create email management endpoints
- Build response generation endpoints
- Setup user preference endpoints
- Implement authentication and authorization
- Add error handling and validation

## 6.1 Email Endpoints

### Email Management API

```python
# backend/app/api/v1/emails.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.core.database import get_db
from app.schemas.email import EmailResponse, EmailStats
from app.models.email import Email
from app.services.email_service import EmailService

router = APIRouter()

@router.get("/", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of emails with optional filters"""
    query = db.query(Email)

    if category:
        query = query.filter(Email.category == category)

    if priority:
        query = query.filter(Email.priority == priority)

    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()
    return emails

@router.get("/stats", response_model=EmailStats)
async def get_email_stats(db: Session = Depends(get_db)):
    """Get email statistics"""
    total_emails = db.query(Email).count()
    unread_count = db.query(Email).filter(Email.processed_at.is_(None)).count()

    category_counts = db.query(
        Email.category,
        func.count(Email.id)
    ).group_by(Email.category).all()

    priority_counts = db.query(
        Email.priority,
        func.count(Email.id)
    ).group_by(Email.priority).all()

    return {
        'total_emails': total_emails,
        'unread_count': unread_count,
        'categories': dict(category_counts),
        'priorities': dict(priority_counts)
    }

@router.post("/sync")
async def sync_emails(db: Session = Depends(get_db)):
    """Trigger email sync from provider"""
    from app.workers.email_processor import fetch_new_emails
    task = fetch_new_emails.delay()

    return {'task_id': task.id, 'status': 'queued'}

@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(email_id: str, db: Session = Depends(get_db)):
    """Get single email by ID"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email

@router.put("/{email_id}/classify")
async def reclassify_email(
    email_id: str,
    category: str,
    priority: str,
    db: Session = Depends(get_db)
):
    """Manually reclassify an email (for feedback/learning)"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.category = category
    email.priority = priority
    db.commit()

    # Store feedback for model improvement
    from app.services.feedback_service import FeedbackService
    feedback_service = FeedbackService()
    feedback_service.record_classification_feedback(
        email_id=email_id,
        corrected_category=category,
        corrected_priority=priority
    )

    return {'status': 'updated'}

@router.delete("/{email_id}")
async def delete_email(email_id: str, db: Session = Depends(get_db)):
    """Delete an email"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    db.delete(email)
    db.commit()

    return {'status': 'deleted'}
```

## 6.2 Response Generation Endpoints

### Response API

```python
# backend/app/api/v1/responses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.schemas.response import ResponseRequest, ResponseGenerated
from app.services.response_generator import ResponseGenerator
from app.models.email import Email
from app.models.generated_response import GeneratedResponse

router = APIRouter()

@router.post("/generate", response_model=ResponseGenerated)
async def generate_response(
    request: ResponseRequest,
    db: Session = Depends(get_db)
):
    """Generate AI response for an email"""
    email = db.query(Email).filter(Email.id == request.email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    generator = ResponseGenerator()
    response_data = generator.generate_response(
        email_subject=email.subject,
        email_body=email.body_text,
        tone=request.tone,
        length=request.length,
        context=request.context
    )

    # Save generated response
    generated_response = GeneratedResponse(
        email_id=email.id,
        response_text=response_data['response_text'],
        tone=response_data['tone'],
        length=response_data['length'],
        model_used=response_data['model_used']
    )

    db.add(generated_response)
    db.commit()
    db.refresh(generated_response)

    return generated_response

@router.post("/send")
async def send_response(
    email_id: str,
    response_text: str,
    db: Session = Depends(get_db)
):
    """Send generated response via email"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Send email via Gmail API
    from app.services.email_service import EmailService
    email_service = EmailService(user_credentials={})  # Get from session

    email_service.send_reply(
        message_id=email.message_id,
        reply_text=response_text
    )

    # Update response record
    response = db.query(GeneratedResponse).filter(
        GeneratedResponse.email_id == email_id
    ).order_by(GeneratedResponse.generation_timestamp.desc()).first()

    if response:
        response.sent_at = func.now()
        response.user_approved = True
        db.commit()

    return {'status': 'sent'}

@router.get("/{email_id}/history")
async def get_response_history(
    email_id: str,
    db: Session = Depends(get_db)
):
    """Get all generated responses for an email"""
    responses = db.query(GeneratedResponse).filter(
        GeneratedResponse.email_id == email_id
    ).order_by(GeneratedResponse.generation_timestamp.desc()).all()

    return responses

@router.put("/{response_id}/feedback")
async def submit_response_feedback(
    response_id: str,
    rating: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback on generated response"""
    response = db.query(GeneratedResponse).filter(
        GeneratedResponse.id == response_id
    ).first()

    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    response.feedback_score = rating
    db.commit()

    # Store in feedback table
    from app.models.user_feedback import UserFeedback
    feedback = UserFeedback(
        response_id=response_id,
        email_id=response.email_id,
        rating=rating,
        comments=comments,
        feedback_type='response_quality'
    )
    db.add(feedback)
    db.commit()

    return {'status': 'feedback_recorded'}
```

## 6.3 User Preferences Endpoints

### Preferences API

```python
# backend/app/api/v1/preferences.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.preferences import PreferencesUpdate, PreferencesResponse
from app.models.user_preferences import UserPreferences

router = APIRouter()

@router.get("/", response_model=PreferencesResponse)
async def get_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if not prefs:
        # Create default preferences
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return prefs

@router.put("/", response_model=PreferencesResponse)
async def update_preferences(
    user_id: str,
    update: PreferencesUpdate,
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")

    # Update fields
    for field, value in update.dict(exclude_unset=True).items():
        setattr(prefs, field, value)

    db.commit()
    db.refresh(prefs)

    return prefs

@router.post("/rules")
async def add_custom_rule(
    user_id: str,
    rule: dict,
    db: Session = Depends(get_db)
):
    """Add custom priority/category rule"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")

    # Add rule to priority_rules JSON field
    priority_rules = prefs.priority_rules or []
    priority_rules.append(rule)
    prefs.priority_rules = priority_rules

    db.commit()

    return {'status': 'rule_added', 'rules': priority_rules}
```

## 6.4 Authentication Endpoints

### Auth API

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    # Verify credentials (implementation depends on auth strategy)
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception

    return user
```

## 6.5 Pydantic Schemas

### Request/Response Schemas

```python
# backend/app/schemas/email.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmailResponse(BaseModel):
    id: str
    subject: str
    sender_email: str
    received_at: datetime
    category: Optional[str]
    priority: Optional[str]
    urgency_score: Optional[float]
    requires_action: bool

    class Config:
        from_attributes = True

class EmailStats(BaseModel):
    total_emails: int
    unread_count: int
    categories: dict
    priorities: dict

# backend/app/schemas/response.py
class ResponseRequest(BaseModel):
    email_id: str
    tone: str = 'professional'
    length: str = 'medium'
    context: Optional[str] = None

class ResponseGenerated(BaseModel):
    id: str
    response_text: str
    tone: str
    length: str
    model_used: str

    class Config:
        from_attributes = True
```

## 6.6 Main API Router

### API Configuration

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import emails, responses, preferences, auth

api_router = APIRouter()

api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(responses.router, prefix="/responses", tags=["responses"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
```

## Deliverables

- ✅ Complete REST API with all endpoints
- ✅ Email CRUD operations
- ✅ Response generation and sending
- ✅ User preferences management
- ✅ Authentication and authorization
- ✅ Request validation with Pydantic
- ✅ Error handling and status codes
- ✅ API documentation (auto-generated)

## Success Criteria

- All endpoints properly documented
- Request/response validation working
- Authentication required for protected routes
- Error responses follow consistent format
- API response time <200ms (95th percentile)
- Proper HTTP status codes used
- CORS configured correctly
- Rate limiting implemented
