from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class GoogleAuthURL(BaseModel):
    authorization_url: str
    state: str


class GoogleCallback(BaseModel):
    code: str
    state: str


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    user_id: str
    email: EmailStr
    access_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
