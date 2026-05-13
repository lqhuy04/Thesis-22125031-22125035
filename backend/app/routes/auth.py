from fastapi import APIRouter, HTTPException, status, Depends
from app.models.auth_schemas import (
    SignupRequest, LoginRequest, AuthResponse, AuthData,
    ForgotPasswordRequest, ResetPasswordRequest, UserResponse, SocialLoginRequest,
    RefreshTokenRequest, LogoutRequest, VerifyOTPRequest, ResetPasswordWithOTPRequest
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
            request.password
        )
        return AuthResponse(
            data=AuthData().dict(),
            errorCode=0,
            errorDesc=result["message"],
            requestId=request_id,
            result=True
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
                refresh_token=result.get("refresh_token")
            ).dict(),
            errorCode=0,
            errorDesc="Login successful",
            requestId=request_id,
            result=True
        )
    except ValueError as e:
        msg = str(e)
        if msg == "Account not verified":
            return AuthResponse(
                data={},
                errorCode=403001,
                errorDesc=msg,
                requestId=request_id,
                result=False
            )
        return AuthResponse(
            data={},
            errorCode=401001,
            errorDesc=msg,
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


@router.post("/verify-email")
async def verify_email(request: VerifyOTPRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.verify_email(request.email, request.otp)
        return {
            "data": result,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
    except ValueError as e:
        return {
            "data": {},
            "errorCode": 400003,
            "errorDesc": str(e),
            "requestId": request_id,
            "result": False
        }
    except Exception:
        return {
            "data": {},
            "errorCode": 500001,
            "errorDesc": "Internal server error",
            "requestId": request_id,
            "result": False
        }


@router.post("/resend-verification-otp")
async def resend_verification_otp(request: ForgotPasswordRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.resend_verification_otp(request.email)
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
        result = await AuthService.google_login(request.token)
        
        return AuthResponse(
            data=AuthData(
                token=result["token"],
                refresh_token=result.get("refresh_token")
            ).dict(),
            errorCode=0,
            errorDesc="Google login successful",
            requestId=request_id,
            result=True
        )
    except ValueError as e:
        return AuthResponse(
            data={},
            errorCode=401002,
            errorDesc=f"Google authentication failed: {str(e)}",
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


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: RefreshTokenRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.refresh_access_token(request.refresh_token)
        return AuthResponse(
            data=AuthData(
                token=result["token"],
                refresh_token=result.get("refresh_token")
            ).dict(),
            errorCode=0,
            errorDesc="Token refreshed successfully",
            requestId=request_id,
            result=True
        )
    except ValueError as e:
        return AuthResponse(
            data={},
            errorCode=401001,
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


@router.post("/logout")
async def logout(request: LogoutRequest):
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.logout(request.refresh_token)
        return {
            "data": result,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
    except ValueError as e:
        return {
            "data": {},
            "errorCode": 500001,
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


@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP sent to email for password reset.
    This endpoint validates the OTP without resetting the password.
    """
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.verify_otp(request.email, request.otp)
        return {
            "data": result,
            "errorCode": 0,
            "errorDesc": "OTP verified successfully",
            "requestId": request_id,
            "result": True
        }
    except ValueError as e:
        return {
            "data": {},
            "errorCode": 400001,
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


@router.post("/reset-password-with-otp")
async def reset_password_with_otp(request: ResetPasswordWithOTPRequest):
    """
    Reset password after OTP verification.
    OTP must be verified before calling this endpoint.
    """
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.reset_password_with_otp(
            request.reset_password_token,
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


@router.post("/resend-otp")
async def resend_otp(request: ForgotPasswordRequest):
    """
    Resend OTP to email. Call this when user didn't receive OTP or it expired.
    Deletes old OTP and generates a new one.
    """
    request_id = str(uuid.uuid4())
    try:
        result = await AuthService.resend_otp(request.email)
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