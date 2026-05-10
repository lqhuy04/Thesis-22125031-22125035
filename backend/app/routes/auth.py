from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import (
    SignupRequest, LoginRequest, AuthResponse, AuthData,
    ForgotPasswordRequest, ResetPasswordRequest, UserResponse, SocialLoginRequest
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user
import uuid

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.signup(
            request.email,
            request.phone_number,
            request.password
        )
        return AuthResponse(
            data=AuthData(
                token=result["token"],
                user_id=result["user_id"],
                email=result["email"]
            ).dict(),
            errorCode=0,
            errorDesc="User registered successfully",
            requestId=request_id,
            result=True,
            userId=result["user_id"]
        )
    except ValueError as e:
        return AuthResponse(
            data={},
            errorCode=409001,
            errorDesc=str(e),
            requestId=request_id,
            result=False
        )
    except Exception as e:
        return AuthResponse(
            data={},
            errorCode=500001,
            errorDesc="Internal server error",
            requestId=request_id,
            result=False
        )

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.login(request.email, request.password)
        return AuthResponse(
            data=AuthData(
                token=result["token"],
                user_id=result["user_id"],
                email=result["email"]
            ).dict(),
            errorCode=0,
            errorDesc="Login successful",
            requestId=request_id,
            result=True,
            userId=result["user_id"]
        )
    except ValueError:
        return AuthResponse(
            data={},
            errorCode=401001,
            errorDesc="Invalid email or password",
            requestId=request_id,
            result=False
        )
    except Exception as e:
        return AuthResponse(
            data={},
            errorCode=500001,
            errorDesc="Internal server error",
            requestId=request_id,
            result=False
        )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.forgot_password(request.email)
        return {
            "data": result,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
    except Exception as e:
        return {
            "data": {},
            "errorCode": 500001,
            "errorDesc": "Internal server error",
            "requestId": request_id,
            "result": False
        }

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.reset_password(
            current_user["email"],
            request.old_password,
            request.new_password,
        )
        return {
            "data": result,
            "errorCode": 0,
            "errorDesc": "Password reset successfully",
            "requestId": request_id,
            "result": True
        }
    except ValueError as e:
        return {
            "data": {},
            "errorCode": 400002,
            "errorDesc": str(e),
            "requestId": request_id,
            "result": False
        }
    except Exception as e:
        return {
            "data": {},
            "errorCode": 500001,
            "errorDesc": "Internal server error",
            "requestId": request_id,
            "result": False
        }

@router.post("/social-login", response_model=AuthResponse)
async def social_login(request: SocialLoginRequest):
    request_id = str(uuid.uuid4())
    try:
        if request.provider == "google":
            result = await AuthService.google_login(request.token)
        elif request.provider == "facebook":
            result = await AuthService.facebook_login(request.token)
        else:
            return AuthResponse(
                data={},
                errorCode=400001,
                errorDesc="Unsupported provider",
                requestId=request_id,
                result=False
            )
        
        return AuthResponse(
            data=AuthData(
                token=result["token"],
                user_id=result["user_id"],
                email=result["email"],
                provider=result.get("provider"),
                avatar_url=result.get("avatar_url")
            ).dict(),
            errorCode=0,
            errorDesc=f"{request.provider.title()} login successful",
            requestId=request_id,
            result=True,
            userId=result["user_id"]
        )
    except ValueError as e:
        return AuthResponse(
            data={},
            errorCode=401002,
            errorDesc=f"{request.provider} authentication failed: {str(e)}",
            requestId=request_id,
            result=False
        )
    except Exception as e:
        return AuthResponse(
            data={},
            errorCode=500001,
            errorDesc="Internal server error",
            requestId=request_id,
            result=False
        )

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        # This is a protected route example
        from app.services.auth_service import supabase
        
        user_result = supabase.table("user").select("id, email, phone_number, provider, avatar_url").eq("id", current_user["user_id"]).execute()
        
        if not user_result.data:
            return {
                "data": {},
                "errorCode": 404001,
                "errorDesc": "User not found",
                "requestId": request_id,
                "result": False
            }
        
        user = user_result.data[0]
        user_data = {
            "user_id": user["id"],
            "email": user["email"],
            "phone_number": user.get("phone_number"),
            "provider": user.get("provider"),
            "avatar_url": user.get("avatar_url")
        }
        
        return {
            "data": user_data,
            "errorCode": 0,
            "errorDesc": "User profile retrieved successfully",
            "requestId": request_id,
            "result": True,
            "userId": user["id"]
        }
    except Exception as e:
        return {
            "data": {},
            "errorCode": 500001,
            "errorDesc": "Internal server error",
            "requestId": request_id,
            "result": False
        }