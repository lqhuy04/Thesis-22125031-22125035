"""Generate a secure key for CHATBOT_API_KEY."""

import secrets


def generate_chatbot_api_key(nbytes: int = 32) -> str:
    """Return a URL-safe random key.

    nbytes=32 gives ~256 bits of entropy.
    """
    return secrets.token_urlsafe(nbytes)


if __name__ == "__main__":
    key = generate_chatbot_api_key()
    print("Generated chatbot key:")
    print(key)
    print("\nAdd this line to your .env:")
    print(f"CHATBOT_API_KEY={key}")
