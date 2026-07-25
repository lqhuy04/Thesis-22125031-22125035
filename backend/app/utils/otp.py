"""Cryptographically secure, single-use OTP storage backed by Redis."""

import hashlib
import hmac
import secrets

from app.config import settings
from app.utils.redis import get_redis_client


class OTPResendCooldownError(ValueError):
    """Raised when a new OTP is requested before the resend cooldown expires."""


class OTPService:
    RESET_SESSION_EXPIRY_MINUTES = 5

    @staticmethod
    def _identity(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _otp_key(email: str, purpose: str) -> str:
        return f"otp:{purpose}:{OTPService._identity(email)}"

    @staticmethod
    def _attempts_key(email: str, purpose: str) -> str:
        return f"otp:attempts:{purpose}:{OTPService._identity(email)}"

    @staticmethod
    def _cooldown_key(email: str, purpose: str) -> str:
        return f"otp:cooldown:{purpose}:{OTPService._identity(email)}"

    @staticmethod
    def _otp_digest(email: str, purpose: str, otp: str) -> str:
        message = f"{purpose}:{OTPService._identity(email)}:{otp}".encode()
        return hmac.new(settings.JWT_SECRET.encode(), message, hashlib.sha256).hexdigest()

    @staticmethod
    def _reset_session_key(token: str) -> str:
        digest = hmac.new(
            settings.JWT_SECRET.encode(), token.encode(), hashlib.sha256
        ).hexdigest()
        return f"otp:reset-session:{digest}"

    @staticmethod
    async def generate_and_store_otp(email: str) -> str:
        return await OTPService.generate_and_store_otp_for_purpose(
            email, "reset-password"
        )

    @staticmethod
    async def generate_and_store_otp_for_purpose(
        email: str,
        purpose: str,
        expiry_minutes: int | None = None,
    ) -> str:
        redis = get_redis_client()
        length = min(max(settings.OTP_LENGTH, 4), 10)
        otp = f"{secrets.randbelow(10 ** length):0{length}d}"
        ttl_seconds = (expiry_minutes or settings.OTP_EXPIRE_MINUTES) * 60
        cooldown = max(settings.OTP_RESEND_COOLDOWN_SECONDS, 1)
        cooldown_key = OTPService._cooldown_key(email, purpose)

        try:
            acquired = await redis.set(cooldown_key, "1", ex=cooldown, nx=True)
            if not acquired:
                remaining = max(await redis.ttl(cooldown_key), 1)
                raise OTPResendCooldownError(
                    f"Please wait {remaining} seconds before requesting another OTP"
                )

            await redis.setex(
                OTPService._otp_key(email, purpose),
                ttl_seconds,
                OTPService._otp_digest(email, purpose, otp),
            )
            await redis.setex(
                OTPService._attempts_key(email, purpose), ttl_seconds, "0"
            )
            return otp
        except OTPResendCooldownError:
            raise
        except Exception as exc:
            await redis.delete(cooldown_key)
            raise RuntimeError("Unable to create OTP") from exc

    @staticmethod
    async def verify_otp(email: str, otp_input: str) -> bool:
        return await OTPService.verify_otp_for_purpose(
            email, otp_input, "reset-password"
        )

    @staticmethod
    async def verify_otp_for_purpose(
        email: str, otp_input: str, purpose: str
    ) -> bool:
        if not otp_input.isdigit() or len(otp_input) != settings.OTP_LENGTH:
            raise ValueError("Invalid OTP")

        redis = get_redis_client()
        key = OTPService._otp_key(email, purpose)
        attempts_key = OTPService._attempts_key(email, purpose)
        candidate = OTPService._otp_digest(email, purpose, otp_input)
        script = """
        local stored = redis.call('GET', KEYS[1])
        if not stored then return {-1, 0} end
        if stored == ARGV[1] then
          redis.call('DEL', KEYS[1], KEYS[2])
          return {1, 0}
        end
        local attempts = redis.call('INCR', KEYS[2])
        local ttl = redis.call('TTL', KEYS[1])
        if ttl > 0 then redis.call('EXPIRE', KEYS[2], ttl) end
        if attempts >= tonumber(ARGV[2]) then
          redis.call('DEL', KEYS[1], KEYS[2])
          return {-2, 0}
        end
        return {0, tonumber(ARGV[2]) - attempts}
        """
        try:
            result, remaining = await redis.eval(
                script, 2, key, attempts_key, candidate, settings.OTP_MAX_ATTEMPTS
            )
        except Exception as exc:
            raise RuntimeError("Unable to verify OTP") from exc

        if result == 1:
            return True
        if result == -1:
            raise ValueError("OTP expired or not found")
        if result == -2:
            raise ValueError("Maximum OTP attempts exceeded. Please request a new OTP")
        raise ValueError(f"Invalid OTP. {remaining} attempts remaining")

    @staticmethod
    async def create_reset_session(email: str) -> str:
        redis = get_redis_client()
        token = secrets.token_urlsafe(32)
        ttl_seconds = OTPService.RESET_SESSION_EXPIRY_MINUTES * 60
        session_key = OTPService._reset_session_key(token)
        email_key = f"otp:reset-session-by-email:{OTPService._identity(email)}"
        try:
            existing_key = await redis.get(email_key)
            if existing_key:
                await redis.delete(existing_key)
            await redis.setex(session_key, ttl_seconds, OTPService._identity(email))
            await redis.setex(email_key, ttl_seconds, session_key)
            return token
        except Exception as exc:
            raise RuntimeError("Unable to create reset session") from exc

    @staticmethod
    async def consume_reset_session(session_token: str) -> str | None:
        redis = get_redis_client()
        session_key = OTPService._reset_session_key(session_token)
        try:
            email = await redis.getdel(session_key)
            if email:
                await redis.delete(f"otp:reset-session-by-email:{email}")
            return email
        except Exception as exc:
            raise RuntimeError("Unable to consume reset session") from exc

    @staticmethod
    async def delete_reset_session(email: str) -> bool:
        redis = get_redis_client()
        email_key = f"otp:reset-session-by-email:{OTPService._identity(email)}"
        try:
            session_key = await redis.get(email_key)
            if session_key:
                await redis.delete(session_key)
            await redis.delete(email_key)
            return True
        except Exception:
            return False

    @staticmethod
    async def delete_otp(email: str) -> bool:
        return await OTPService.delete_otp_for_purpose(email, "reset-password")

    @staticmethod
    async def delete_otp_for_purpose(email: str, purpose: str) -> bool:
        redis = get_redis_client()
        try:
            await redis.delete(
                OTPService._otp_key(email, purpose),
                OTPService._attempts_key(email, purpose),
            )
            return True
        except Exception:
            return False

    @staticmethod
    async def check_otp_exists(email: str) -> bool:
        return await OTPService.check_otp_exists_for_purpose(
            email, "reset-password"
        )

    @staticmethod
    async def check_otp_exists_for_purpose(email: str, purpose: str) -> bool:
        try:
            return bool(
                await get_redis_client().exists(
                    OTPService._otp_key(email, purpose)
                )
            )
        except Exception:
            return False
