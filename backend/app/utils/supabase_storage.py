import logging
import re
from urllib.parse import quote
from typing import Any, List, Dict
from supabase import create_client, Client
from app.config import settings
from app.utils.user_namespace import user_namespace

logger = logging.getLogger(__name__)

BUCKET_NAME = "backtests"
_BACKTEST_FILENAME = re.compile(r"^[A-Za-z0-9._-]{1,160}_backtest\.json$")


def _validated_filename(filename: str) -> str:
    normalized = str(filename or "").strip()
    if not _BACKTEST_FILENAME.fullmatch(normalized):
        raise ValueError("Invalid backtest filename")
    return normalized


def _user_object_path(user_id: str, filename: str) -> str:
    return f"{user_namespace(user_id)}/{_validated_filename(filename)}"

def get_supabase_client() -> Client:
    """Initialize and return a Supabase Client using settings configurations."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_backtest_file(
    user_id: str,
    file_path: str,
    filename: str,
    content_type: str,
) -> str:
    """
    Upload a file and return its authenticated API proxy URL.
    """
    try:
        supabase = get_supabase_client()
        
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        safe_filename = _validated_filename(filename)
        object_path = _user_object_path(user_id, safe_filename)
        supabase.storage.from_(BUCKET_NAME).upload(
            path=object_path,
            file=file_data,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        protected_url = f"/api/agentic/backtests/files/{quote(safe_filename)}"
        logger.info("Successfully uploaded a user-owned backtest to private storage")
        return protected_url
    except Exception as e:
        logger.error(f"Failed to upload {filename} to Supabase Storage: {e}")
        raise e

def list_backtest_files(user_id: str) -> List[Dict[str, Any]]:
    """
    List JSON files owned by the authenticated user.
    """
    try:
        supabase = get_supabase_client()
        owner = user_namespace(user_id)
        files_list = supabase.storage.from_(BUCKET_NAME).list(path=owner)
        
        results = []
        for file in files_list:
            name = file.get("name") if isinstance(file, dict) else getattr(file, "name", "")
            if name and name.endswith(".json"):
                created_at = file.get("created_at") if isinstance(file, dict) else getattr(file, "created_at", None)
                results.append({
                    "name": name,
                    "created_at": created_at,
                    "json_url": f"/api/agentic/backtests/files/{quote(name)}"
                })
        
        # Sort alphabetically by name descending (effectively sorting by timestamp in name)
        results.sort(key=lambda x: x["name"], reverse=True)
        return results
    except Exception as e:
        logger.error(f"Failed to list backtest files from Supabase Storage: {e}")
        return []


def download_backtest_file(user_id: str, filename: str) -> bytes:
    """Download one object owned by the authenticated user."""
    object_path = _user_object_path(user_id, filename)
    return get_supabase_client().storage.from_(BUCKET_NAME).download(object_path)
