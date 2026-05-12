"""
Redis-backed session and token management service.
Stores access tokens and refresh tokens in Redis with TTL.
Enables token revocation (logout) and session validation.
"""

from datetime import timedelta
from app.utils.redis import get_redis_client
from app.config import settings


class RedisSessionService:
    """Manage user sessions and tokens in Redis"""
    
    @staticmethod
    async def store_access_token(user_id: str, token: str) -> bool:
        """
        Store access token in Redis with TTL.
        Key format: session:access:{user_id}
        """
        redis = get_redis_client()
        ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        key = f"session:access:{user_id}"
        
        try:
            await redis.setex(key, ttl_seconds, token)
            return True
        except Exception as e:
            print(f"Failed to store access token: {str(e)}")
            return False
    
    @staticmethod
    async def store_refresh_token(user_id: str, token: str) -> bool:
        """
        Store refresh token in Redis with TTL.
        Key format: session:refresh:{user_id}
        """
        redis = get_redis_client()
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        key = f"session:refresh:{user_id}"
        
        try:
            await redis.setex(key, ttl_seconds, token)
            return True
        except Exception as e:
            print(f"Failed to store refresh token: {str(e)}")
            return False
    
    @staticmethod
    async def validate_access_token(user_id: str, token: str) -> bool:
        """
        Validate if access token exists in Redis and matches.
        Returns True only if token is in Redis and matches stored token.
        """
        redis = get_redis_client()
        key = f"session:access:{user_id}"
        
        try:
            stored_token = await redis.get(key)
            return stored_token is not None and stored_token == token
        except Exception as e:
            print(f"Failed to validate access token: {str(e)}")
            return False
    
    @staticmethod
    async def validate_refresh_token(user_id: str, token: str) -> bool:
        """
        Validate if refresh token exists in Redis and matches.
        Returns True only if token is in Redis and matches stored token.
        """
        redis = get_redis_client()
        key = f"session:refresh:{user_id}"
        
        try:
            stored_token = await redis.get(key)
            return stored_token is not None and stored_token == token
        except Exception as e:
            print(f"Failed to validate refresh token: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_access_token(user_id: str) -> bool:
        """
        Delete access token from Redis (logout).
        """
        redis = get_redis_client()
        key = f"session:access:{user_id}"
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"Failed to revoke access token: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_refresh_token(user_id: str) -> bool:
        """
        Delete refresh token from Redis.
        """
        redis = get_redis_client()
        key = f"session:refresh:{user_id}"
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"Failed to revoke refresh token: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_all_sessions(user_id: str) -> bool:
        """
        Delete both access and refresh tokens (full logout).
        """
        redis = get_redis_client()
        access_key = f"session:access:{user_id}"
        refresh_key = f"session:refresh:{user_id}"
        
        try:
            await redis.delete(access_key, refresh_key)
            return True
        except Exception as e:
            print(f"Failed to revoke all sessions: {str(e)}")
            return False
    
    @staticmethod
    async def get_access_token(user_id: str) -> str | None:
        """
        Get stored access token from Redis.
        """
        redis = get_redis_client()
        key = f"session:access:{user_id}"
        
        try:
            return await redis.get(key)
        except Exception as e:
            print(f"Failed to get access token: {str(e)}")
            return None
    
    @staticmethod
    async def get_refresh_token(user_id: str) -> str | None:
        """
        Get stored refresh token from Redis.
        """
        redis = get_redis_client()
        key = f"session:refresh:{user_id}"
        
        try:
            return await redis.get(key)
        except Exception as e:
            print(f"Failed to get refresh token: {str(e)}")
            return None
