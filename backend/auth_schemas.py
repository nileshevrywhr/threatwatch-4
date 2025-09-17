from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid
import re

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Enforce password requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    subscription_tier: str
    subscription_status: str
    monitoring_terms_count: int
    quick_scans_today: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: uuid.UUID

class LoginResponse(BaseModel):
    user: UserResponse
    token: Token
    message: str = "Login successful"

class SubscriptionCreate(BaseModel):
    term: str
    email: EmailStr

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    term: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Payment schemas
class CheckoutRequest(BaseModel):
    plan: str = Field(..., description="Subscription plan: 'pro' or 'enterprise'")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect if payment is cancelled")

class CheckoutResponse(BaseModel):
    url: str
    session_id: str

class PaymentStatusResponse(BaseModel):
    status: str
    payment_status: str
    subscription_tier: Optional[str]
    message: str