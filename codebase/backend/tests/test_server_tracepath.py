"""Tests for API response traceability."""

from __future__ import annotations

import unittest

from server import _adapt_response


class ServerTracepathTests(unittest.TestCase):
    def test_tracepath_exposes_openrouter_model_and_usage(self):
        response = _adapt_response(
            {
                "route": "ANSWER",
                "intent": "ask_deadline",
                "confidence": 0.9,
                "grounding_status": "grounded",
                "response": "Câu trả lời",
                "citations": [],
                "llm": {
                    "called": True,
                    "provider": "openrouter",
                    "status": "success",
                    "model": "openai/gpt-4o-mini",
                    "usage": {
                        "prompt_tokens": 20,
                        "completion_tokens": 10,
                        "total_tokens": 30,
                    },
                },
            },
            latency_ms=123,
        )

        trace = response["tracepath"]
        self.assertTrue(trace["llm_called"])
        self.assertEqual(trace["model"], "openai/gpt-4o-mini")
        self.assertEqual(trace["usage"]["total_tokens"], 30)
        self.assertTrue(
            any(tool["name"].startswith("OpenRouter") for tool in trace["tools_used"])
        )


if __name__ == "__main__":
    unittest.main()
