from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")
    return OpenAI(api_key=api_key)
