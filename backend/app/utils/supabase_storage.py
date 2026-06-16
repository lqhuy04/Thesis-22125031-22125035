import logging
import os
from typing import Any, List, Dict
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "backtests"

def get_supabase_client() -> Client:
    """Initialize and return a Supabase Client using settings configurations."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_backtest_file(file_path: str, filename: str, content_type: str) -> str:
    """
    Uploads a file to Supabase Storage and returns its public URL.
    """
    try:
        supabase = get_supabase_client()
        
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=file_data,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
        logger.info(f"Successfully uploaded {filename} to Supabase Storage: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to upload {filename} to Supabase Storage: {e}")
        raise e

def list_backtest_files() -> List[Dict[str, Any]]:
    """
    Lists all json files in the 'backtests' bucket.
    """
    try:
        supabase = get_supabase_client()
        files_list = supabase.storage.from_(BUCKET_NAME).list()
        
        results = []
        for file in files_list:
            name = file.get("name") if isinstance(file, dict) else getattr(file, "name", "")
            if name and name.endswith(".json"):
                created_at = file.get("created_at") if isinstance(file, dict) else getattr(file, "created_at", None)
                json_url = supabase.storage.from_(BUCKET_NAME).get_public_url(name)
                
                results.append({
                    "name": name,
                    "created_at": created_at,
                    "json_url": json_url
                })
        
        # Sort alphabetically by name descending (effectively sorting by timestamp in name)
        results.sort(key=lambda x: x["name"], reverse=True)
        return results
    except Exception as e:
        logger.error(f"Failed to list backtest files from Supabase Storage: {e}")
        return []
