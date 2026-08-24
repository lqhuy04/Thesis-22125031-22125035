import unittest
from unittest.mock import AsyncMock, patch

from app.services.auth_service import AuthService


class AuthRefreshRotationTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.services.auth_service.create_refresh_token")
    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.verify_token")
    @patch(
        "app.services.auth_service.RedisSessionService.store_refresh_token",
        new_callable=AsyncMock,
    )
    @patch(
        "app.services.auth_service.RedisSessionService.store_access_token",
        new_callable=AsyncMock,
    )
    @patch(
        "app.services.auth_service.RedisSessionService.validate_refresh_token",
        new_callable=AsyncMock,
    )
    async def test_refresh_rotates_access_and_refresh_tokens(
        self,
        validate_refresh,
        store_access,
        store_refresh,
        verify_token,
        create_access,
        create_refresh,
    ):
        verify_token.return_value = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "session_id": "browser-session",
        }
        validate_refresh.return_value = True
        store_access.return_value = True
        store_refresh.return_value = True
        create_access.return_value = "new-access"
        create_refresh.return_value = "new-refresh"

        result = await AuthService.refresh_access_token("old-refresh")

        self.assertEqual(result["token"], "new-access")
        self.assertEqual(result["refresh_token"], "new-refresh")
        validate_refresh.assert_awaited_once_with(
            "admin-id",
            "old-refresh",
            session_id="browser-session",
        )
        create_access.assert_called_once_with(
            "admin-id",
            "admin@example.com",
            session_id="browser-session",
        )
        create_refresh.assert_called_once_with(
            "admin-id",
            "admin@example.com",
            session_id="browser-session",
        )
        store_access.assert_awaited_once_with(
            "admin-id",
            "new-access",
            session_id="browser-session",
        )
        store_refresh.assert_awaited_once_with(
            "admin-id",
            "new-refresh",
            session_id="browser-session",
        )


if __name__ == "__main__":
    unittest.main()
