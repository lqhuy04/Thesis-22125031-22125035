import unittest
from unittest.mock import AsyncMock, patch

from app.services.redis_session_service import RedisSessionService


class RedisMultiSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_tokens_are_stored_under_independent_session_keys(self):
        redis = AsyncMock()

        with patch(
            "app.services.redis_session_service.get_redis_client",
            return_value=redis,
        ):
            first = await RedisSessionService.store_refresh_token(
                "user-1", "refresh-a", session_id="browser-a"
            )
            second = await RedisSessionService.store_refresh_token(
                "user-1", "refresh-b", session_id="mobile-b"
            )

        self.assertTrue(first)
        self.assertTrue(second)
        stored_keys = [call.args[0] for call in redis.setex.await_args_list]
        self.assertEqual(
            stored_keys,
            [
                "session:refresh:user-1:browser-a",
                "session:refresh:user-1:mobile-b",
            ],
        )

    async def test_logout_revokes_only_selected_session(self):
        redis = AsyncMock()

        with patch(
            "app.services.redis_session_service.get_redis_client",
            return_value=redis,
        ):
            result = await RedisSessionService.revoke_session(
                "user-1", "browser-a"
            )

        self.assertTrue(result)
        redis.delete.assert_awaited_once_with(
            "session:access:user-1:browser-a",
            "session:refresh:user-1:browser-a",
        )
        redis.srem.assert_awaited_once_with(
            "session:index:user-1", "browser-a"
        )


if __name__ == "__main__":
    unittest.main()
