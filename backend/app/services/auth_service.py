from supabase import create_client, Client
from app.config import settings
from app.utils.password import hash_password, verify_password
from app.utils.token import create_access_token, create_refresh_token, verify_token
from app.utils.email import send_reset_email, send_verification_email
from app.utils.otp import OTPService
from app.services.redis_session_service import RedisSessionService
import httpx
import google.auth.transport.requests
import google.oauth2.id_token
import uuid
from typing import Optional

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
class AuthService:
    @staticmethod
    async def signup(email: str, password: str):
        # Check if user exists
        existing = supabase.table("User").select("*").eq("email", email).execute()
        if existing.data:
            raise ValueError("User already exists")
        
        # Create user
        hashed_pwd = hash_password(password)
        new_user = supabase.table("User").insert({
            "email": email,
            "hash_password": hashed_pwd,
            "status": "unverified"
        }).execute()
        
        if not new_user.data:
            raise ValueError("Failed to create user")
        
        user_data = new_user.data[0]

        # Generate and send verification OTP after account creation
        verification_otp = await OTPService.generate_and_store_otp_for_purpose(email, "verify-email")
        await send_verification_email(user_data["email"], verification_otp)
        
        return {
            "message": "Registration successful. Please verify your email before logging in."
        }
    
    @staticmethod
    async def login(email: str, password: str):
        # Find user
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            raise ValueError("Invalid credentials")
        
        user = user_result.data[0]
        
        # Verify password
        if not verify_password(password, user["hash_password"]):
            raise ValueError("Invalid credentials")

        # Block login until email is verified
        if user.get("status") != "verified":
            raise ValueError("Account not verified")
        
        # Generate tokens
        access_token = create_access_token(user["id"], user["email"])
        refresh_token = create_refresh_token(user["id"], user["email"])
        
        # Store tokens in Redis
        await RedisSessionService.store_access_token(user["id"], access_token)
        await RedisSessionService.store_refresh_token(user["id"], refresh_token)
        
        return {
            "token": access_token,
            "refresh_token": refresh_token,
            "user_id": user["id"],
            "email": user["email"]
        }

    @staticmethod
    async def verify_email(email: str, otp: str):
        user_result = supabase.table("User").select("*").eq("email", email).execute()

        if not user_result.data:
            raise ValueError("Invalid verification code")

        user = user_result.data[0]
        if user.get("status") == "verified":
            return {"message": "Email already verified"}

        is_valid = await OTPService.verify_otp_for_purpose(email, otp, "verify-email")
        if not is_valid:
            raise ValueError("Invalid verification code")

        result = supabase.table("User").update({
            "status": "verified"
        }).eq("id", user["id"]).execute()

        if not result.data:
            raise ValueError("Failed to verify email")

        return {"message": "Email verified successfully"}

    @staticmethod
    async def resend_verification_otp(email: str):
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            return {"message": "If the email exists, a new verification OTP has been sent"}

        user = user_result.data[0]
        if user.get("status") == "verified":
            return {"message": "Email already verified"}

        await OTPService.delete_otp_for_purpose(email, "verify-email")
        verification_otp = await OTPService.generate_and_store_otp_for_purpose(email, "verify-email")
        await send_verification_email(email, verification_otp)

        return {"message": "If the email exists, a new verification OTP has been sent"}
    
    @staticmethod
    async def reset_password(email: str, old_password: Optional[str], new_password: str, confirm_new_password: str):
        if new_password != confirm_new_password:
            raise ValueError("Confirm password does not match new password")

        # Find user
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            raise ValueError("Invalid email or password")

        user = user_result.data[0]

        has_password = bool(user.get("hash_password"))

        # Verify current password only for accounts that already have one
        if has_password:
            if not old_password:
                raise ValueError("Old password is required")
            if not verify_password(old_password, user["hash_password"]):
                raise ValueError("Invalid email or password")

        # Update password
        hashed_pwd = hash_password(new_password)
        result = supabase.table("User").update({
            "hash_password": hashed_pwd
        }).eq("id", user["id"]).execute()
        
        if not result.data:
            raise ValueError("Failed to reset password")
        
        return {"message": "Password reset successfully"}
    
    @staticmethod
    async def forgot_password(email: str):
        # Find user
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, an OTP has been sent"}
        
        user = user_result.data[0]
        
        # Generate OTP and store in Redis
        otp = await OTPService.generate_and_store_otp(email)
        
        # Send OTP via email
        await send_reset_email(email, otp)
        
        return {"message": "If the email exists, an OTP has been sent"}
    

    
    @staticmethod
    async def verify_otp(email: str, otp: str):
        """
        Verify OTP sent to email.
        
        Args:
            email: User email address
            otp: OTP provided by user
            
        Returns:
            Success message
            
        Raises:
            ValueError: If OTP is invalid or expired
        """
        try:
            # Verify the OTP
            is_valid = await OTPService.verify_otp(email, otp)
            
            if is_valid:
                reset_password_token = await OTPService.create_reset_session(email)
                return {
                    "message": "OTP verified successfully",
                    "reset_password_token": reset_password_token,
                    "expires_in_minutes": OTPService.RESET_SESSION_EXPIRY_MINUTES,
                }
            else:
                raise ValueError("Invalid OTP")
                
        except Exception as e:
            raise ValueError(str(e))
    
    @staticmethod
    async def reset_password_with_otp(reset_password_token: str, new_password: str):
        """
        Reset password after OTP verification.
        Requires a short-lived reset session token issued by verify_otp.
        
        Args:
            reset_password_token: Short-lived token issued after OTP verification
            new_password: New password to set
            
        Returns:
            Success message with user info
            
        Raises:
            ValueError: If user not found or update fails
        """
        email = await OTPService.consume_reset_session(reset_password_token)
        if not email:
            raise ValueError("Reset session expired or invalid")

        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            raise ValueError("User not found")

        user = user_result.data[0]

        # Update password
        hashed_pwd = hash_password(new_password)
        result = supabase.table("User").update({
            "hash_password": hashed_pwd
        }).eq("id", user["id"]).execute()
        
        if not result.data:
            raise ValueError("Failed to reset password")
        
        return {
            "message": "Password reset successfully",
        }
    
    @staticmethod
    async def resend_otp(email: str):
        """
        Resend OTP to email. Deletes old OTP and generates a new one.
        
        Args:
            email: User email address
            
        Returns:
            Success message
            
        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a new OTP has been sent"}
        
        # Delete old OTP if exists
        await OTPService.delete_otp(email)
        await OTPService.delete_reset_session(email)
        
        # Generate new OTP and store in Redis
        otp = await OTPService.generate_and_store_otp(email)
        
        # Send OTP via email
        await send_reset_email(email, otp)
        
        return {"message": "If the email exists, a new OTP has been sent"}
    
    @staticmethod
    async def google_login(token: str):
        """Authenticate user with Google OAuth token"""
        try:
            valid_client_ids = [
                settings.GOOGLE_CLIENT_ID,           # Web
                settings.GOOGLE_IOS_CLIENT_ID,       # iOS
                settings.GOOGLE_ANDROID_CLIENT_ID,   # Android
            ]
            
            # Verify Google token
            request = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                token, request, valid_client_ids
            )
            
            # Extract user information
            email = id_info.get('email')
            
            if not email:
                raise ValueError("Email not provided by Google")
            
            # Check if user exists
            user_result = supabase.table("User").select("*").eq("email", email).execute()
            
            if user_result.data:
                # User exists, update their info
                user = user_result.data[0]
                update_data = {}
                supabase.table("User").update(update_data).eq("id", user["id"]).execute()
            else:
                # Create new user
                new_user = supabase.table("User").insert({
                    "email": email,
                    "status": "verified",
                    "hash_password": ""  # No password for OAuth users
                }).execute()
                
                if not new_user.data:
                    raise ValueError("Failed to create user")
                user = new_user.data[0]
            
            # Create access token and refresh token
            access_token = create_access_token(user["id"], user["email"])
            refresh_token = create_refresh_token(user["id"], user["email"])
            
            # Store tokens in Redis
            await RedisSessionService.store_access_token(user["id"], access_token)
            await RedisSessionService.store_refresh_token(user["id"], refresh_token)
            
            return {
                "token": access_token,
                "refresh_token": refresh_token,
                "user_id": user["id"],
                "email": user["email"],
            }
            
        except Exception as e:
            raise ValueError(f"Google authentication failed: {str(e)}")
    
    @staticmethod
    async def refresh_access_token(refresh_token: str):
        """
        Validate refresh token and issue a new access token.
        """
        # Verify refresh token is valid JWT
        try:
            payload = verify_token(refresh_token, "refresh")
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

        user_id = payload.get("user_id")
        email = payload.get("email")
        
        # Verify refresh token exists in Redis
        is_valid = await RedisSessionService.validate_refresh_token(user_id, refresh_token)
        if not is_valid:
            raise ValueError("Refresh token not found or invalid")
        
        # Generate new access token
        new_access_token = create_access_token(user_id, email)
        
        # Store new access token in Redis
        await RedisSessionService.store_access_token(user_id, new_access_token)
        
        return {
            "token": new_access_token,
            "user_id": user_id,
            "email": email
        }
    
    @staticmethod
    async def logout(refresh_token: str):
        """
        Revoke all tokens for a user (logout).
        """
        try:
            payload = verify_token(refresh_token, "refresh")
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

        user_id = payload.get("user_id")

        success = await RedisSessionService.revoke_all_sessions(user_id)
        if not success:
            raise ValueError("Failed to logout")
        
        return {"message": "Logged out successfully"}
    
    @staticmethod
    async def verify_google_token(token: str):
        """Helper method to verify Google OAuth token and return user info"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
                )
                if response.status_code != 200:
                    raise ValueError("Invalid Google token")
                return response.json()
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
    
    @staticmethod
    async def verify_facebook_token(token: str):
        """Helper method to verify Facebook access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/me?access_token={token}&fields=id,email,name,picture"
                )
                if response.status_code != 200:
                    raise ValueError("Invalid Facebook token")
                return response.json()
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")