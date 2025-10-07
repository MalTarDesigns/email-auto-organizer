from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import GoogleAuthURL, AuthResponse

router = APIRouter()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]


def get_oauth_flow(state: str = None) -> Flow:
    """Create OAuth flow object"""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    return flow


@router.get("/google/login", response_model=GoogleAuthURL)
async def google_login():
    """Initiate Google OAuth flow"""
    try:
        flow = get_oauth_flow()

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return GoogleAuthURL(
            authorization_url=authorization_url,
            state=state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate OAuth flow: {str(e)}"
        )


@router.get("/google/callback", response_model=AuthResponse)
async def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens
        flow = get_oauth_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info from Google
        user_info = get_user_info(credentials)

        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info['id']).first()

        # Calculate token expiration
        token_expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp()) if credentials.expiry else None

        if user:
            # Update existing user
            user.access_token = credentials.token
            user.refresh_token = credentials.refresh_token or user.refresh_token
            user.token_expires_at = token_expires_at
            user.email = user_info['email']
            user.name = user_info.get('name', user.name)
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                google_id=user_info['id'],
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expires_at=token_expires_at
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        return AuthResponse(
            status="authenticated",
            user_id=str(user.id),
            email=user.email,
            access_token=credentials.token
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


def get_user_info(credentials: Credentials) -> Dict[str, Any]:
    """Get user information from Google"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token available"
            )

        # Create credentials object
        credentials = Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )

        # Refresh the token
        from google.auth.transport.requests import Request
        credentials.refresh(Request())

        # Update user with new tokens
        user.access_token = credentials.token
        if credentials.refresh_token:
            user.refresh_token = credentials.refresh_token
        user.token_expires_at = credentials.expiry
        user.updated_at = datetime.utcnow()

        db.commit()

        return {
            "status": "success",
            "access_token": credentials.token,
            "expires_at": credentials.expiry
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )
