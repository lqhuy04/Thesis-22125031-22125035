from supabase import create_client, Client
from app.config import settings
from app.utils.password import hash_password, verify_password
from app.utils.token import create_access_token, create_reset_token
from app.services.email_service import send_reset_email

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class AuthService:
    @staticmethod
    async def signup(email: str, phone_number: str, password: str):
        # Check if user exists
        existing = supabase.table("user").select("*").eq("email", email).execute()
        if existing.data:
            raise ValueError("User already exists")
        
        # Create user
        hashed_pwd = hash_password(password)
        new_user = supabase.table("user").insert({
            "email": email,
            "phone_number": phone_number,
            "hash_password": hashed_pwd
        }).execute()
        
        if not new_user.data:
            raise ValueError("Failed to create user")
        
        user_data = new_user.data[0]
        token = create_access_token(user_data["id"], user_data["email"])
        
        return {
            "token": token,
            "user_id": user_data["id"],
            "email": user_data["email"]
        }
    
    @staticmethod
    async def login(email: str, password: str):
        # Find user
        user_result = supabase.table("user").select("*").eq("email", email).execute()
        if not user_result.data:
            raise ValueError("Invalid credentials")
        
        user = user_result.data[0]
        
        # Verify password
        if not verify_password(password, user["hash_password"]):
            raise ValueError("Invalid credentials")
        
        token = create_access_token(user["id"], user["email"])
        
        return {
            "token": token,
            "user_id": user["id"],
            "email": user["email"]
        }
    
    @staticmethod
    async def forgot_password(email: str):
        # Find user
        user_result = supabase.table("user").select("*").eq("email", email).execute()
        if not user_result.data:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        user = user_result.data[0]
        reset_token = create_reset_token(user["id"], user["email"])
        
        # Send email
        await send_reset_email(email, reset_token)
        
        return {"message": "If the email exists, a reset link has been sent"}
    
    @staticmethod
    async def reset_password(token: str, new_password: str):
        from app.utils.token import verify_token
        
        # Verify token
        try:
            payload = verify_token(token, token_type="reset")
        except ValueError as e:
            raise ValueError(str(e))
        
        user_id = payload.get("user_id")
        
        # Update password
        hashed_pwd = hash_password(new_password)
        result = supabase.table("user").update({
            "hash_password": hashed_pwd
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise ValueError("Failed to reset password")
        
        return {"message": "Password reset successfully"}