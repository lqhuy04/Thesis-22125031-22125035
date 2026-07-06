from dotenv import load_dotenv
from openai import OpenAI
import os
import threading

load_dotenv()

# A single shared OpenAI client for the whole app.
#
# Previously this factory returned a brand-new OpenAI() on every call, and every
# node in the analyze/chatbot graphs called it (orchestrator, aggregator,
# intent_classifier, qa/chat/market agents). Each OpenAI() opens its own httpx
# connection pool that was never closed, so file descriptors/sockets leaked with
# every request and eventually surfaced as intermittent
# "[Errno 35] Resource temporarily unavailable" (EAGAIN) errors.
#
# The client is thread-safe, so a single instance can be shared across the
# FastAPI threadpool and the batch ThreadPoolExecutor used by admin analysis.
_client: OpenAI | None = None
_client_lock = threading.Lock()


def _get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("Missing OPENAI_API_KEY in environment.")
                _client = OpenAI(api_key=api_key)
    return _client
