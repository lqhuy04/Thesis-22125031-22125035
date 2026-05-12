from supabase import create_client, Client
from app.config import settings
from app.utils.password import hash_password, verify_password
from app.utils.token import create_access_token, create_refresh_token, create_reset_token, verify_token
from app.utils.email import send_reset_email, send_verification_email
from app.services.redis_session_service import RedisSessionService
import httpx
import google.auth.transport.requests
import google.oauth2.id_token
import facebook
import uuid

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
        verification_token = str(uuid.uuid4())
        new_user = supabase.table("User").insert({
            "email": email,
            "hash_password": hashed_pwd,
            "status": "unverified",
            "verification_token": verification_token
        }).execute()
        
        if not new_user.data:
            raise ValueError("Failed to create user")
        
        user_data = new_user.data[0]

        # Send verification email after account creation
        await send_verification_email(user_data["email"], verification_token)
        
        return {
            "user_id": user_data["id"],
            "email": user_data["email"],
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
            raise ValueError("Email is not verified")
        
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
    async def verify_email(token: str):
        user_result = supabase.table("User").select("*").eq("verification_token", token).execute()

        if not user_result.data:
            raise ValueError("Invalid verification token")

        user = user_result.data[0]
        if user.get("status") == "verified":
            return {"message": "Email already verified"}

        result = supabase.table("User").update({
            "status": "verified",
            "verification_token": None
        }).eq("id", user["id"]).execute()

        if not result.data:
            raise ValueError("Failed to verify email")

        return {"message": "Email verified successfully"}
    
    @staticmethod
    async def forgot_password(email: str):
        # Find user
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        user = user_result.data[0]
        reset_token = create_reset_token(user["id"], user["email"])
        
        # Send email
        await send_reset_email(email, reset_token)
        
        return {"message": "If the email exists, a reset link has been sent"}
    
    @staticmethod
    async def reset_password(email: str, old_password: str, new_password: str):
        # Find user
        user_result = supabase.table("User").select("*").eq("email", email).execute()
        if not user_result.data:
            raise ValueError("Invalid email or password")

        user = user_result.data[0]

        # Verify current password before updating
        if not user.get("hash_password") or not verify_password(old_password, user["hash_password"]):
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
    async def google_login(token: str):
        """Authenticate user with Google OAuth token"""
        try:
            # Verify Google token
            request = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                token, request, settings.GOOGLE_CLIENT_ID
            )
            
            # Extract user information
            email = id_info.get('email')
            name = id_info.get('name', '')
            avatar_url = id_info.get('picture', '')
            
            if not email:
                raise ValueError("Email not provided by Google")
            
            # Check if user exists
            user_result = supabase.table("User").select("*").eq("email", email).execute()
            
            if user_result.data:
                # User exists, update their info
                user = user_result.data[0]
                update_data = {
                    "provider": "google",
                    "avatar_url": avatar_url
                }
                supabase.table("User").update(update_data).eq("id", user["id"]).execute()
            else:
                # Create new user
                new_user = supabase.table("User").insert({
                    "email": email,
                    "provider": "google",
                    "avatar_url": avatar_url,
                    "status": "verified",
                    "verification_token": None,
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
                "provider": "google",
                "avatar_url": avatar_url
            }
            
        except Exception as e:
            raise ValueError(f"Google authentication failed: {str(e)}")
    
    @staticmethod
    async def facebook_login(token: str):
        """Authenticate user with Facebook access token"""
        try:
            # Create Facebook GraphAPI instance
            graph = facebook.GraphAPI(access_token=token)
            
            # Get user profile information
            profile = graph.get_object('me', fields='id,email,name,picture')
            
            # Debug: Print what Facebook returns
            print(f"Facebook profile data: {profile}")
            
            email = profile.get('email')
            facebook_id = profile.get('id')
            name = profile.get('name', '')
            avatar_url = profile.get('picture', {}).get('data', {}).get('url', '')
            
            # If no email, use Facebook ID as identifier
            if not email:
                email = f"facebook_{facebook_id}@facebook.local"  # Create a dummy email
                print(f"No email provided by Facebook, using dummy email: {email}")
            
            # Check if user exists by email first, then by Facebook ID if not found
            user_result = supabase.table("User").select("*").eq("email", email).execute()
            
            # If no user found by email, try to find by Facebook ID
            if not user_result.data:
                user_result = supabase.table("User").select("*").eq("facebook_id", facebook_id).execute()
            
            if user_result.data:
                # User exists, update their info
                user = user_result.data[0]
                update_data = {
                    "provider": "facebook",
                    "avatar_url": avatar_url,
                    "facebook_id": facebook_id
                }
                supabase.table("User").update(update_data).eq("id", user["id"]).execute()
            else:
                # Create new user
                new_user = supabase.table("User").insert({
                    "email": email,
                    "provider": "facebook",
                    "avatar_url": avatar_url,
                    "facebook_id": facebook_id,
                    "status": "verified",
                    "verification_token": None,
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
                "provider": "facebook",
                "avatar_url": avatar_url
            }
            
        except Exception as e:
            raise ValueError(f"Facebook authentication failed: {str(e)}")
    
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