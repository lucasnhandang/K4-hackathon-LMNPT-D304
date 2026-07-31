"""Tests for frontend/backend error handling."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import httpx

from ai_router import (
    BACKEND_TIMEOUT_SECONDS,
    call_backend_api_async,
    transform_backend_response_to_ui,
)


class _FailingClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json):
        raise httpx.ConnectError("connection refused")


class _SuccessfulResponse:
    status_code = 200

    @staticmethod
    def json():
        return {
            "status": "resolved",
            "intent": "help",
            "confidence": 0.9,
            "action": "direct_answer",
            "response": "OK",
            "citations": [],
            "handoff": False,
        }


class _CapturingClient:
    def __init__(self):
        self.payload = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json):
        self.payload = json
        return _SuccessfulResponse()


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

    async def test_frontend_sends_k4_cohort(self):
        client = _CapturingClient()
        with patch("ai_router.httpx.AsyncClient", return_value=client):
            await call_backend_api_async("Gate yêu cầu gì?")

        self.assertEqual(
            client.payload["learning_context"]["cohort"],
            "k4",
        )

    async def test_frontend_uses_supplied_session_id(self):
        client = _CapturingClient()
        with patch("ai_router.httpx.AsyncClient", return_value=client):
            await call_backend_api_async(
                "deadline hôm nào z",
                session_id="discord_session_test_user",
            )

        self.assertEqual(
            client.payload["metadata"]["session_id"],
            "discord_session_test_user",
        )

    def test_escalation_ui_does_not_claim_ticket_was_sent(self):
        result = transform_backend_response_to_ui(
            {
                "status": "escalated",
                "intent": "ask_deadline",
                "confidence": 0.9,
                "action": "escalate_mod",
                "response": "Cần Mod xác nhận.",
                "citations": [],
                "handoff": True,
            }
        )

        self.assertEqual(result["title"], "Cần Mentor/Mod xác nhận")
        self.assertNotIn("đã tự động", result["title"].lower())
        self.assertIn("chưa tự động gửi", result["escalate_detail"].lower())


if __name__ == "__main__":
    unittest.main()
