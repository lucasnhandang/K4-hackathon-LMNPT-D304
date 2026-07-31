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

    def test_out_of_domain_is_rejected_without_handoff(self):
        response = _adapt_response(
            {
                "route": "ANSWER",
                "intent": "out_of_domain",
                "confidence": 0.95,
                "grounding_status": "no_source",
                "response": "Ngoài phạm vi khóa học.",
                "citations": [],
                "llm": None,
            },
            latency_ms=10,
        )

        self.assertEqual(response["status"], "out_of_scope")
        self.assertEqual(response["action"], "reject")
        self.assertFalse(response["handoff"])

    def test_conflict_reason_is_preserved_in_tracepath(self):
        response = _adapt_response(
            {
                "route": "ESCALATE",
                "intent": "ask_deadline",
                "confidence": 0.9,
                "grounding_status": "no_source",
                "response": "Các nguồn chính thức đang mâu thuẫn.",
                "citations": [],
                "escalation": {
                    "reason_code": "conflicting_sources",
                    "target": "MOD",
                },
                "llm": None,
            },
            latency_ms=10,
        )

        trace = response["tracepath"]
        self.assertEqual(trace["grounding_status"], "conflict")
        self.assertIn("Grounding: conflict", trace["steps"][1])
        self.assertTrue(
            any(
                tool["status"] == "conflict"
                for tool in trace["tools_used"]
            )
        )


if __name__ == "__main__":
    unittest.main()
