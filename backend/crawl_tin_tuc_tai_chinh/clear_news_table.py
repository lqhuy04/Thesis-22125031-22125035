"""
Database utility functions for news management
"""
from supabase import create_client, Client
from app.config import get_settings
from dotenv import load_dotenv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app', '.env')
load_dotenv(env_path)

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


async def clear_news_table():
    """
    Clear all data from the financial_news table
    WARNING: This will delete all news data!
    """
    try:
        # Delete all records
        result = supabase.table("financial_news").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("✓ News table cleared successfully")
        return True
    except Exception as e:
        print(f"✗ Error clearing table: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    import sys
    
    print("⚠️  WARNING: This will delete ALL news data from the database!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        asyncio.run(clear_news_table())
        print("Done.")
    else:
        print("Cancelled.")
