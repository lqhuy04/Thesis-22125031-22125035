"""Small Redis-backed fixed-window limiter for sensitive API operations."""

import hashlib
import logging

from fastapi import HTTPException, Request, status

from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Use the ASGI-provided peer address; proxy trust stays a server concern."""
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(
    scope: str,
    identifier: str,
    *,
    limit: int,
    window_seconds: int,
) -> None:
    digest = hashlib.sha256(identifier.strip().lower().encode()).hexdigest()
    key = f"rate-limit:{scope}:{digest}"
    script = """
    local count = redis.call('INCR', KEYS[1])
    if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
    return {count, redis.call('TTL', KEYS[1])}
    """
    try:
        count, ttl = await get_redis_client().eval(
            script, 1, key, window_seconds
        )
    except Exception:
        # Authentication must remain available during a Redis incident; token
        # session validation already fails closed for protected operations.
        logger.exception("Rate limiter unavailable for scope %s", scope)
        return

    if count > limit:
        retry_after = max(int(ttl), 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
