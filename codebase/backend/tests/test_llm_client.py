"""Tests for the OpenRouter LLM client.

Uses mocked HTTP responses to avoid real API calls.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chatbot_tools.llm_client import (
    LLMClient,
    LLMConfig,
    LLMError,
    load_backend_env,
)


class LLMConfigTests(unittest.TestCase):
    """Test LLMConfig initialization and defaults."""

    def test_default_config(self):
        config = LLMConfig()
        self.assertEqual(config.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(config.model, "google/gemini-2.0-flash-001")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 1)
        self.assertFalse(config.api_key)

    def test_custom_config(self):
        config = LLMConfig(api_key="test-key", model="custom/model")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "custom/model")

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "env-key", "OPENROUTER_MODEL": "test/model"})
    def test_from_env(self):
        config = LLMConfig.from_env()
        self.assertEqual(config.api_key, "env-key")
        self.assertEqual(config.model, "test/model")

    @patch.dict("os.environ", {}, clear=True)
    def test_from_env_missing(self):
        config = LLMConfig.from_env()
        self.assertFalse(config.api_key)

    def test_load_backend_env_uses_explicit_path_without_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "OPENROUTER_API_KEY=file-key\nOPENROUTER_MODEL=file/model\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "exported-key"},
                clear=True,
            ):
                loaded = load_backend_env(env_path)
                self.assertTrue(loaded)
                self.assertEqual(
                    os.environ["OPENROUTER_API_KEY"],
                    "exported-key",
                )
                self.assertEqual(os.environ["OPENROUTER_MODEL"], "file/model")


class LLMClientTests(unittest.TestCase):
    """Test LLMClient with mocked HTTP."""

    def setUp(self):
        self.config = LLMConfig(api_key="test-key", model="test/model")
        self.client = LLMClient(self.config)

    def test_is_available_with_key(self):
        self.assertTrue(self.client.is_available())

    def test_is_available_without_key(self):
        client = LLMClient(LLMConfig(api_key=""))
        self.assertFalse(client.is_available())

    def test_chat_success(self):
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Xin chào!"},
                    "finish_reason": "stop",
                }
            ],
            "model": "test/model",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = self.client.chat([
                {"role": "user", "content": "Hello"}
            ])

            self.assertEqual(result.content, "Xin chào!")
            self.assertEqual(result.model, "test/model")
            self.assertEqual(result.usage["total_tokens"], 15)
            self.assertEqual(result.finish_reason, "stop")

    def test_chat_http_error(self):
        import urllib.error

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="test", code=429, msg="Rate limited",
                hdrs=None, fp=MagicMock(read=MagicMock(return_value=b'{"error": "rate limited"}'))
            )

            with self.assertRaises(LLMError) as ctx:
                self.client.chat([{"role": "user", "content": "Hello"}])

            self.assertIn("429", str(ctx.exception))

    def test_chat_network_error(self):
        import urllib.error

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with self.assertRaises(LLMError) as ctx:
                self.client.chat([{"role": "user", "content": "Hello"}])

            self.assertIn("Network error", str(ctx.exception))

    def test_chat_invalid_json_response(self):
        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"not json"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            with self.assertRaises(LLMError):
                self.client.chat([{"role": "user", "content": "Hello"}])

    def test_chat_empty_choices(self):
        mock_response = {"choices": [], "model": "test/model"}

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            with self.assertRaises(LLMError):
                self.client.chat([{"role": "user", "content": "Hello"}])

    def test_chat_custom_params(self):
        mock_response = {
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "model": "custom/model",
            "usage": {},
        }

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = self.client.chat(
                [{"role": "user", "content": "Hello"}],
                model="custom/model",
                temperature=0.9,
                max_tokens=500,
            )

            # Verify the request was sent with correct params
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["model"], "custom/model")
            self.assertEqual(body["temperature"], 0.9)
            self.assertEqual(body["max_tokens"], 500)

    def test_chat_sends_and_parses_tool_calls(self):
        tool_calls = [
            {
                "id": "call_route",
                "type": "function",
                "function": {
                    "name": "route_student_request",
                    "arguments": '{"scope":"out_of_scope"}',
                },
            }
        ]
        mock_response = {
            "choices": [
                {
                    "message": {"content": None, "tool_calls": tool_calls},
                    "finish_reason": "tool_calls",
                }
            ],
            "model": "test/model",
            "usage": {"total_tokens": 25},
        }
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "route_student_request",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        with patch("chatbot_tools.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = self.client.chat(
                [{"role": "user", "content": "Route me"}],
                tools=tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "route_student_request"},
                },
                parallel_tool_calls=False,
            )

        request = mock_urlopen.call_args[0][0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["tools"], tools)
        self.assertFalse(body["parallel_tool_calls"])
        self.assertEqual(result.content, "")
        self.assertEqual(result.tool_calls, tool_calls)

    def test_retry_on_http_error(self):
        import urllib.error

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    url="test", code=500, msg="Server error",
                    hdrs=None, fp=MagicMock(read=MagicMock(return_value=b'error'))
                )
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "choices": [{"message": {"content": "OK after retry"}, "finish_reason": "stop"}],
                "model": "test/model",
                "usage": {},
            }).encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("chatbot_tools.llm_client.urllib.request.urlopen", side_effect=side_effect):
            result = self.client.chat([{"role": "user", "content": "Hello"}])
            self.assertEqual(result.content, "OK after retry")
            self.assertEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()
