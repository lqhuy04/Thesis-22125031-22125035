"""Redis-backed token storage with support for multiple user sessions."""

from app.utils.redis import get_redis_client
from app.config import settings


class RedisSessionService:
    """Manage user sessions and tokens in Redis"""

    @staticmethod
    def _token_key(token_type: str, user_id: str, session_id: str | None) -> str:
        # Tokens issued before multi-session support use the original key so
        # active clients can still refresh once and migrate to a session key.
        suffix = f":{session_id}" if session_id else ""
        return f"session:{token_type}:{user_id}{suffix}"

    @staticmethod
    def _session_index_key(user_id: str) -> str:
        return f"session:index:{user_id}"

    @staticmethod
    async def _remember_session(redis, user_id: str, session_id: str | None) -> None:
        if not session_id:
            return
        index_key = RedisSessionService._session_index_key(user_id)
        await redis.sadd(index_key, session_id)
        await redis.expire(
            index_key,
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        )
    
    @staticmethod
    async def store_access_token(
        user_id: str,
        token: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Store access token in Redis with TTL.
        Key format: session:access:{user_id}:{session_id}
        """
        redis = get_redis_client()
        ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        key = RedisSessionService._token_key("access", user_id, session_id)
        
        try:
            await redis.setex(key, ttl_seconds, token)
            await RedisSessionService._remember_session(redis, user_id, session_id)
            return True
        except Exception as e:
            print(f"Failed to store access token: {str(e)}")
            return False
    
    @staticmethod
    async def store_refresh_token(
        user_id: str,
        token: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Store refresh token in Redis with TTL.
        Key format: session:refresh:{user_id}:{session_id}
        """
        redis = get_redis_client()
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        key = RedisSessionService._token_key("refresh", user_id, session_id)
        
        try:
            await redis.setex(key, ttl_seconds, token)
            await RedisSessionService._remember_session(redis, user_id, session_id)
            return True
        except Exception as e:
            print(f"Failed to store refresh token: {str(e)}")
            return False
    
    @staticmethod
    async def validate_access_token(
        user_id: str,
        token: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Validate if access token exists in Redis and matches.
        Returns True only if token is in Redis and matches stored token.
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("access", user_id, session_id)
        
        try:
            stored_token = await redis.get(key)
            return stored_token is not None and stored_token == token
        except Exception as e:
            print(f"Failed to validate access token: {str(e)}")
            return False
    
    @staticmethod
    async def validate_refresh_token(
        user_id: str,
        token: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Validate if refresh token exists in Redis and matches.
        Returns True only if token is in Redis and matches stored token.
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("refresh", user_id, session_id)
        
        try:
            stored_token = await redis.get(key)
            return stored_token is not None and stored_token == token
        except Exception as e:
            print(f"Failed to validate refresh token: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_access_token(user_id: str, session_id: str | None = None) -> bool:
        """
        Delete access token from Redis (logout).
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("access", user_id, session_id)
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"Failed to revoke access token: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_refresh_token(user_id: str, session_id: str | None = None) -> bool:
        """
        Delete refresh token from Redis.
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("refresh", user_id, session_id)
        
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
        index_key = RedisSessionService._session_index_key(user_id)

        try:
            session_ids = await redis.smembers(index_key)
            keys = [
                RedisSessionService._token_key("access", user_id, None),
                RedisSessionService._token_key("refresh", user_id, None),
                index_key,
            ]
            for session_id in session_ids:
                keys.extend(
                    [
                        RedisSessionService._token_key("access", user_id, session_id),
                        RedisSessionService._token_key("refresh", user_id, session_id),
                    ]
                )
            await redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Failed to revoke all sessions: {str(e)}")
            return False
    
    @staticmethod
    async def revoke_session(user_id: str, session_id: str) -> bool:
        """Revoke only one browser/device session."""
        redis = get_redis_client()
        index_key = RedisSessionService._session_index_key(user_id)
        try:
            await redis.delete(
                RedisSessionService._token_key("access", user_id, session_id),
                RedisSessionService._token_key("refresh", user_id, session_id),
            )
            await redis.srem(index_key, session_id)
            return True
        except Exception as e:
            print(f"Failed to revoke session: {str(e)}")
            return False

    @staticmethod
    async def get_access_token(
        user_id: str,
        session_id: str | None = None,
    ) -> str | None:
        """
        Get stored access token from Redis.
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("access", user_id, session_id)
        
        try:
            return await redis.get(key)
        except Exception as e:
            print(f"Failed to get access token: {str(e)}")
            return None
    
    @staticmethod
    async def get_refresh_token(
        user_id: str,
        session_id: str | None = None,
    ) -> str | None:
        """
        Get stored refresh token from Redis.
        """
        redis = get_redis_client()
        key = RedisSessionService._token_key("refresh", user_id, session_id)
        
        try:
            return await redis.get(key)
        except Exception as e:
            print(f"Failed to get refresh token: {str(e)}")
            return None
