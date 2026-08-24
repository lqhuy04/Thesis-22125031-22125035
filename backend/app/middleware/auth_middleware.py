from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.token import verify_token
from app.services.redis_session_service import RedisSessionService

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from JWT token and validate in Redis.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = verify_token(token, token_type="access")
        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        
        # Validate token exists in Redis (enables logout/revocation)
        is_valid = await RedisSessionService.validate_access_token(
            user_id,
            token,
            session_id=session_id,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that requires the authenticated user to have role = 'admin'.

    Role is read from the User table (authoritative, always fresh) rather than
    the JWT, so promoting/demoting a user takes effect without re-issuing tokens.
    """
    # Lazy import to avoid an import cycle at module load time.
    from app.services.auth_service import supabase

    user_id = current_user["user_id"]
    try:
        res = (
            supabase.table("User")
            .select("role")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin role",
        )

    rows = getattr(res, "data", None) or []
    role = rows[0].get("role") if rows else None

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return {**current_user, "role": role}
