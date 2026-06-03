import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Stockrium"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    # Connection string Postgres của Supabase (khác SUPABASE_URL là REST endpoint).
    # Dùng cho LangGraph PostgresSaver lưu lịch sử chat.
    SUPABASE_DB_URL: str = ""
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    RESET_TOKEN_EXPIRATION_MINUTES: int = 30
    
    # Token TTL (for Redis session storage)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OTP Settings
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 15
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Email (for password reset)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    # Frontend URL (for password reset links)
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_IOS_CLIENT_ID: str = ""
    GOOGLE_ANDROID_CLIENT_ID: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    
    # SSI FC Data API Settings
    SSI_CONSUMER_ID: str = ""
    SSI_CONSUMER_SECRET: str = ""
    SSI_AUTH_TYPE: str = "Bearer"
    SSI_API_URL: str = "https://fc-data.ssi.com.vn/"
    SSI_STREAM_URL: str = "https://fc-datahub.ssi.com.vn/"

    GEMINI_API_KEY: str
    OPENAI_API_KEY: str = ""
    CHATBOT_API_KEY: str = ""

    # Serper
    SERPER_API_URL: str = "https://google.serper.dev/search"
    SERPER_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()


# SSI Config object for the ssi-fc-data library
class SSIConfig:
    """Configuration class compatible with ssi-fc-data library"""
    def __init__(self):
        self.auth_type = settings.SSI_AUTH_TYPE
        self.consumerID = settings.SSI_CONSUMER_ID
        self.consumerSecret = settings.SSI_CONSUMER_SECRET
        self.url = settings.SSI_API_URL
        self.stream_url = settings.SSI_STREAM_URL

def get_ssi_config():
    return SSIConfig()