from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class SignupRequest(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v is None:
            return v
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^\+?\d{10,15}$', phone):
            raise ValueError('Invalid phone number format')
        return phone


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    email: str
    phone_number: Optional[str] = None