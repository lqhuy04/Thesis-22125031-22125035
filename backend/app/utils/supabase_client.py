"""
Shared Supabase client.

Previously every service/util module called ``create_client(...)`` at import
time, so the app ended up with ~9 independent Supabase clients, each holding its
own httpx connection pool (default ``max_connections=100``). Under bursty load
this multiplied the number of open sockets/file descriptors and contributed to
intermittent ``[Errno 35] Resource temporarily unavailable`` (EAGAIN) errors.

This module exposes a single shared client so the whole app reuses one pooled
httpx connection pool. It also lowers the PostgREST request timeout from the
120s default to 20s so a stalled query cannot hold a worker thread for minutes.

Importing this module goes through ``supabase.create_client`` (the attribute is
monkeypatched in ``app.config`` to suppress a noisy stdout warning), so importing
``app.config`` first keeps that behaviour.
"""
import supabase as _supabase_module
from supabase import Client, ClientOptions

from app.config import settings

_client_options = ClientOptions(
    postgrest_client_timeout=30,
    storage_client_timeout=20,
)

# Single shared client for the whole backend. Reused by every service module.
supabase: Client = _supabase_module.create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY,
    options=_client_options,
)


def get_supabase() -> Client:
    """Return the shared Supabase client."""
    return supabase
