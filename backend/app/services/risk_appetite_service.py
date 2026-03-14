"""
Risk Appetite Service
Handles database operations for user risk appetite
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class RiskAppetiteService:
    """Service for risk appetite database operations"""

    @staticmethod
    async def get_risk_appetite_by_user(user_id: str) -> Optional[Dict]:
        """
        Get risk appetite record for a specific user

        Args:
            user_id: The authenticated user's ID

        Returns:
            Risk appetite record or None
        """
        try:
            result = supabase.table("risk_appetite") \
                .select("*") \
                .eq("userid", user_id) \
                .limit(1) \
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            print(f"Error fetching risk appetite: {e}")
            raise ValueError(f"Failed to fetch risk appetite: {str(e)}")

    @staticmethod
    async def upsert_risk_appetite(
        user_id: str,
        experience: Optional[str] = None,
        expectation: Optional[str] = None,
        period: Optional[str] = None,
        comfort_zone: Optional[str] = None,
        capital_ratio: Optional[str] = None,
    ) -> Dict:
        """
        Create or update risk appetite for a user.
        If a record already exists for the user, it will be updated.

        Args:
            user_id: The authenticated user's ID
            experience: Investment experience level
            expectation: Return expectation
            period: Investment time horizon
            comfort_zone: Risk comfort zone
            capital_ratio: Capital ratio for investment
        """
        try:
            payload = {
                "userid": user_id,
                "experience": experience,
                "expectation": expectation,
                "period": period,
                "comfort_zone": comfort_zone,
                "capital_ratio": capital_ratio,
            }

            # Check if record already exists
            existing = supabase.table("risk_appetite") \
                .select("id") \
                .eq("userid", user_id) \
                .limit(1) \
                .execute()

            if existing.data:
                # Update existing record
                result = supabase.table("risk_appetite") \
                    .update(payload) \
                    .eq("userid", user_id) \
                    .execute()
            else:
                # Insert new record
                result = supabase.table("risk_appetite") \
                    .insert(payload) \
                    .execute()
            
            return result.data[0] if result.data else payload

        except Exception as e:
            print(f"Error upserting risk appetite: {e}")
            raise ValueError(f"Failed to save risk appetite: {str(e)}")
