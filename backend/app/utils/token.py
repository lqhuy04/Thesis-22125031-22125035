import jwt
from datetime import datetime, timedelta
from app.config import settings

def create_access_token(user_id: str, email: str, session_id: str | None = None) -> str:
    expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "type": "access"
    }
    if session_id:
        payload["session_id"] = session_id
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: str, email: str, session_id: str | None = None) -> str:
    expiration = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "type": "refresh"
    }
    if session_id:
        payload["session_id"] = session_id
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_reset_token(user_id: str, email: str) -> str:
    expiration = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRATION_MINUTES)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "type": "reset"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
