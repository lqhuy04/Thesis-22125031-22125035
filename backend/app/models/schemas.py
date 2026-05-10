from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class SignupRequest(BaseModel):
    email: EmailStr
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
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
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
    data: dict = {}
    errorCode: int = 0
    errorDesc: str = ""
    requestId: str
    result: bool
    userId: Optional[str] = None


class AuthData(BaseModel):
    token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    provider: Optional[str] = None
    avatar_url: Optional[str] = None


class SocialLoginRequest(BaseModel):
    token: str
    provider: str = Field(..., pattern='^(google|facebook)$')


class UserResponse(BaseModel):
    user_id: str
    email: str
    phone_number: Optional[str] = None
    provider: Optional[str] = None
    avatar_url: Optional[str] = None