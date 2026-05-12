"""
OTP (One-Time Password) utility module.
Generates, stores, and validates OTPs using Redis with TTL.
"""

import random
import string
import uuid
from app.utils.redis import get_redis_client
from app.config import settings


class OTPService:
    """Manage OTP generation and validation using Redis"""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10  # OTP valid for 10 minutes
    RESET_SESSION_EXPIRY_MINUTES = 5  # Short-lived session after OTP verification
    MAX_OTP_ATTEMPTS = 5  # Max attempts before OTP expires

    @staticmethod
    def _otp_key(email: str, purpose: str) -> str:
        return f"otp:{purpose}:{email}"

    @staticmethod
    def _attempts_key(email: str, purpose: str) -> str:
        return f"otp:attempts:{purpose}:{email}"
    
    @staticmethod
    async def generate_and_store_otp(email: str) -> str:
        return await OTPService.generate_and_store_otp_for_purpose(email, "reset-password")

    @staticmethod
    async def generate_and_store_otp_for_purpose(email: str, purpose: str, expiry_minutes: int | None = None) -> str:
        """
        Generate a 6-digit OTP and store in Redis for a specific purpose.
        
        Args:
            email: User email address
            
        Returns:
            Generated OTP string
            
        Raises:
            Exception: If Redis operation fails
        """
        redis = get_redis_client()
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=OTPService.OTP_LENGTH))
        
        ttl_minutes = expiry_minutes or OTPService.OTP_EXPIRY_MINUTES
        ttl_seconds = ttl_minutes * 60
        key = OTPService._otp_key(email, purpose)
        attempts_key = OTPService._attempts_key(email, purpose)
        
        try:
            # Store OTP
            await redis.setex(key, ttl_seconds, otp)
            
            # Initialize attempts counter
            await redis.setex(attempts_key, ttl_seconds, "0")
            
            return otp
        except Exception as e:
            raise Exception(f"Failed to store OTP: {str(e)}")
    
    @staticmethod
    async def verify_otp(email: str, otp_input: str) -> bool:
        return await OTPService.verify_otp_for_purpose(email, otp_input, "reset-password")

    @staticmethod
    async def verify_otp_for_purpose(email: str, otp_input: str, purpose: str) -> bool:
        """
        Verify if the provided OTP matches the stored OTP in Redis.
        
        Args:
            email: User email address
            otp_input: OTP provided by user
            
        Returns:
            True if OTP is valid, False otherwise
            
        Raises:
            Exception: If max attempts exceeded or Redis fails
        """
        redis = get_redis_client()
        key = OTPService._otp_key(email, purpose)
        attempts_key = OTPService._attempts_key(email, purpose)
        
        try:
            # Get current OTP from Redis
            stored_otp = await redis.get(key)
            
            if not stored_otp:
                raise Exception("OTP expired or not found")
            
            # Get and check attempts
            attempts = await redis.get(attempts_key)
            current_attempts = int(attempts) if attempts else 0
            
            if current_attempts >= OTPService.MAX_OTP_ATTEMPTS:
                # Delete OTP if max attempts exceeded
                await redis.delete(key)
                await redis.delete(attempts_key)
                raise Exception("Maximum OTP attempts exceeded. Please request a new OTP")
            
            # Verify OTP
            if stored_otp == otp_input:
                # Delete OTP after successful verification
                await redis.delete(key)
                await redis.delete(attempts_key)
                return True
            else:
                # Increment attempts counter
                await redis.incr(attempts_key)
                remaining_attempts = OTPService.MAX_OTP_ATTEMPTS - (current_attempts + 1)
                raise Exception(f"Invalid OTP. {remaining_attempts} attempts remaining")
        
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    async def create_reset_session(email: str) -> str:
        """
        Create a short-lived reset session token after OTP verification.

        The token is the only proof required to unlock password reset.
        """
        redis = get_redis_client()
        session_token = str(uuid.uuid4())
        ttl_seconds = OTPService.RESET_SESSION_EXPIRY_MINUTES * 60
        session_key = f"otp:reset-session:{session_token}"
        email_key = f"otp:reset-session-by-email:{email}"

        try:
            existing_session_token = await redis.get(email_key)
            if existing_session_token:
                await redis.delete(f"otp:reset-session:{existing_session_token}")

            await redis.setex(session_key, ttl_seconds, email)
            await redis.setex(email_key, ttl_seconds, session_token)
            return session_token
        except Exception as e:
            raise Exception(f"Failed to create reset session: {str(e)}")

    @staticmethod
    async def consume_reset_session(session_token: str) -> str | None:
        """
        Consume a reset session token once. Returns the email if valid.
        """
        redis = get_redis_client()
        session_key = f"otp:reset-session:{session_token}"

        try:
            email = await redis.get(session_key)
            if not email:
                return None

            await redis.delete(session_key)
            await redis.delete(f"otp:reset-session-by-email:{email}")
            return email
        except Exception as e:
            raise Exception(f"Failed to consume reset session: {str(e)}")

    @staticmethod
    async def delete_reset_session(email: str) -> bool:
        """Delete any reset session associated with an email."""
        redis = get_redis_client()
        email_key = f"otp:reset-session-by-email:{email}"

        try:
            session_token = await redis.get(email_key)
            if session_token:
                await redis.delete(f"otp:reset-session:{session_token}")
            await redis.delete(email_key)
            return True
        except Exception as e:
            print(f"Failed to delete reset session: {str(e)}")
            return False
    
    @staticmethod
    async def delete_otp(email: str) -> bool:
        return await OTPService.delete_otp_for_purpose(email, "reset-password")

    @staticmethod
    async def delete_otp_for_purpose(email: str, purpose: str) -> bool:
        """
        Delete OTP from Redis (for cleanup).
        
        Args:
            email: User email address
            
        Returns:
            True if successful
        """
        redis = get_redis_client()
        key = OTPService._otp_key(email, purpose)
        attempts_key = OTPService._attempts_key(email, purpose)
        
        try:
            await redis.delete(key)
            await redis.delete(attempts_key)
            return True
        except Exception as e:
            print(f"Failed to delete OTP: {str(e)}")
            return False
    
    @staticmethod
    async def check_otp_exists(email: str) -> bool:
        return await OTPService.check_otp_exists_for_purpose(email, "reset-password")

    @staticmethod
    async def check_otp_exists_for_purpose(email: str, purpose: str) -> bool:
        """
        Check if OTP exists for the given email.
        
        Args:
            email: User email address
            
        Returns:
            True if OTP exists, False otherwise
        """
        redis = get_redis_client()
        key = OTPService._otp_key(email, purpose)
        
        try:
            otp = await redis.get(key)
            return otp is not None
        except Exception as e:
            print(f"Failed to check OTP: {str(e)}")
            return False
