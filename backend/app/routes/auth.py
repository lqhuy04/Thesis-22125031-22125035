from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import (
    SignupRequest, LoginRequest, AuthResponse,
    ForgotPasswordRequest, ResetPasswordRequest, UserResponse
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    try:
        result = await AuthService.signup(
            request.email,
            request.phone_number,
            request.password
        )
        return AuthResponse(
            success=True,
            message="User registered successfully",
            **result
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    try:
        result = await AuthService.login(request.email, request.password)
        return AuthResponse(
            success=True,
            message="Login successful",
            **result
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        result = await AuthService.forgot_password(request.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    try:
        result = await AuthService.reset_password(request.token, request.new_password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # This is a protected route example
    from app.services.auth_service import supabase
    
    user_result = supabase.table("user").select("id, email, phone_number").eq("id", current_user["user_id"]).execute()
    
    if not user_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user = user_result.data[0]
    return UserResponse(
        user_id=user["id"],
        email=user["email"],
        phone_number=user.get("phone_number")
    )