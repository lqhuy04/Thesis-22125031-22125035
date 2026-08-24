"""Safe filesystem/storage namespace derived from an authenticated user ID."""

import re


_USER_NAMESPACE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def user_namespace(user_id: str) -> str:
    """Return a path-safe user namespace or reject an invalid token subject."""
    normalized = str(user_id or "").strip()
    if not _USER_NAMESPACE.fullmatch(normalized):
        raise ValueError("Invalid authenticated user ID")
    return normalized
