"""Tests for frontend/backend error handling."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import httpx

from ai_router import BACKEND_TIMEOUT_SECONDS, call_backend_api_async


class _FailingClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json):
        raise httpx.ConnectError("connection refused")


class FrontendBackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_backend_failure_is_not_silently_replaced_by_mock(self):
        with (
            patch("ai_router.httpx.AsyncClient", return_value=_FailingClient()),
            patch("ai_router.classify_and_route", MagicMock()) as local_mock,
        ):
            result = await call_backend_api_async("Deadline AI Log")

        self.assertEqual(result["type"], "SYSTEM_ERROR")
        self.assertIn("không chuyển sang dữ liệu mock", result["message"])
        local_mock.assert_not_called()

    def test_backend_timeout_allows_openrouter_request_to_finish(self):
        self.assertEqual(BACKEND_TIMEOUT_SECONDS, 40.0)


if __name__ == "__main__":
    unittest.main()
