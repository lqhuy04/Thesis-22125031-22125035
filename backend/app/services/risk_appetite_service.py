"""
Risk Appetite Service
Handles database operations for user risk appetite
"""
from app.utils.supabase_client import supabase
from app.config import settings
from typing import Optional, Dict


class RiskAppetiteService:
    """Service for risk appetite database operations"""

    @staticmethod
    def get_risk_appetite_by_user(user_id: str) -> Optional[Dict]:
        """
        Get risk appetite record for a specific user

        Args:
            user_id: The authenticated user's ID

        Returns:
            Risk appetite record or None
        """
        try:
            result = supabase.table("RiskAppetite") \
                .select("*") \
                .eq("userid", user_id) \
                .limit(1) \
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            print(f"Error fetching risk appetite: {e}")
            raise ValueError(f"Failed to fetch risk appetite: {str(e)}")

    @staticmethod
    def upsert_risk_appetite(
        user_id: str,
        period: str,
    ) -> Dict:
        """
        Create or update risk appetite for a user.
        If a record already exists for the user, it will be updated.

        Args:
            user_id: The authenticated user's ID
            period: Investment time horizon (short_term, mid_term, long_term)
        """
        try:
            payload = {
                "userid": user_id,
                "period": period,
            }

            # Check if record already exists
            existing = supabase.table("RiskAppetite") \
                .select("id") \
                .eq("userid", user_id) \
                .limit(1) \
                .execute()

            if existing.data:
                # Update existing record
                result = supabase.table("RiskAppetite") \
                    .update(payload) \
                    .eq("userid", user_id) \
                    .execute()
            else:
                # Insert new record
                result = supabase.table("RiskAppetite") \
                    .insert(payload) \
                    .execute()
            
            return result.data[0] if result.data else payload

        except Exception as e:
            print(f"Error upserting risk appetite: {e}")
            raise ValueError(f"Failed to save risk appetite: {str(e)}")
