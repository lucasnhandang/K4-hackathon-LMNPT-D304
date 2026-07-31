from __future__ import annotations

import json
import unittest

from chatbot_tools.llm_orchestrator import (
    LLMChatbotOrchestrator,
    OpenRouterConfig,
    OpenRouterError,
)


class FakeRegistry:
    def __init__(self) -> None:
        self.executions: list[tuple[str, dict]] = []

    def definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "name": "lookup_deadline",
                "description": "Tra deadline chính thức.",
                "parameters": {
                    "type": "object",
                    "properties": {"assignment": {"type": "string"}},
                    "required": ["assignment"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        ]

    def execute(self, name: str, arguments: dict) -> dict:
        self.executions.append((name, arguments))
        return {
            "status": "ok",
            "data": {"assignment": arguments["assignment"], "deadline": "2026-08-01"},
            "citations": [
                {
                    "source_id": "deadline-source",
                    "title": "Lịch khóa học",
                    "locator": "Mục deadline",
                    "quote": "Hạn nộp ngày 01/08/2026.",
                    "updated_at": "2026-07-31T00:00:00Z",
                }
            ],
            "missing_fields": [],
            "conflicts": [],
            "message": "",
        }


class FakeFallback:
    def process_message(self, **_: object) -> dict:
        return {
            "schema_version": "1.0",
            "message_id": "fallback-message",
            "route": "ANSWER",
            "intent": "greeting",
            "confidence": 0.9,
            "grounding_status": "not_required",
            "response": "Fallback response",
            "clarification": None,
            "citations": [],
            "escalation": None,
            "trace_id": "fallback-trace",
        }


def config(*, fallback_to_rules: bool = True) -> OpenRouterConfig:
    return OpenRouterConfig(
        api_key="test-key",
        base_url="https://openrouter.invalid/api/v1",
        model="test/tool-model",
        app_name="test",
        site_url="http://localhost",
        fallback_to_rules=fallback_to_rules,
    )


class TestLLMChatbotOrchestrator(unittest.TestCase):
    def test_executes_tool_and_returns_only_backend_citations(self) -> None:
        registry = FakeRegistry()
        calls: list[dict] = []
        responses = iter(
            [
                {
                    "model": "test/tool-model",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": "lookup_deadline",
                                            "arguments": json.dumps(
                                                {"assignment": "Weekly Assignment"}
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"total_tokens": 20},
                },
                {
                    "model": "test/tool-model",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "route": "ANSWER",
                                        "intent": "ask_deadline",
                                        "confidence": 0.9,
                                        "grounding_status": "grounded",
                                        "response": "Deadline là ngày 01/08/2026.",
                                        "clarification": None,
                                        "escalation": None,
                                        "citations": [{"source_id": "fabricated"}],
                                    }
                                ),
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 12,
                        "completion_tokens": 8,
                        "total_tokens": 20,
                    },
                },
            ]
        )

        def transport(payload: dict) -> dict:
            calls.append(payload)
            return next(responses)

        chatbot = LLMChatbotOrchestrator(
            registry=registry,  # type: ignore[arg-type]
            config=config(),
            transport=transport,
            fallback=FakeFallback(),  # type: ignore[arg-type]
        )
        result = chatbot.process_message("Deadline Weekly Assignment là khi nào?")

        self.assertEqual(len(calls), 2)
        self.assertEqual(
            registry.executions,
            [("lookup_deadline", {"assignment": "weekly_assignment"})],
        )
        self.assertEqual(result["route"], "ANSWER")
        self.assertEqual(result["runtime"]["engine"], "openrouter")
        self.assertTrue(result["runtime"]["llm_called"])
        self.assertEqual(result["runtime"]["tool_calls"], ["lookup_deadline"])
        self.assertEqual(result["citations"][0]["source_id"], "deadline-source")
        self.assertNotEqual(result["citations"][0]["source_id"], "fabricated")

        second_messages = calls[1]["messages"]
        self.assertEqual(second_messages[-1]["role"], "tool")
        self.assertEqual(second_messages[-1]["tool_call_id"], "call-1")

    def test_falls_back_to_rules_when_provider_fails(self) -> None:
        def failed_transport(_: dict) -> dict:
            raise OpenRouterError("provider unavailable")

        chatbot = LLMChatbotOrchestrator(
            registry=FakeRegistry(),  # type: ignore[arg-type]
            config=config(fallback_to_rules=True),
            transport=failed_transport,
            fallback=FakeFallback(),  # type: ignore[arg-type]
        )
        result = chatbot.process_message("Xin chào")

        self.assertEqual(result["response"], "Fallback response")
        self.assertEqual(result["runtime"]["engine"], "rules_fallback")
        self.assertTrue(result["runtime"]["llm_called"])
        self.assertEqual(result["runtime"]["fallback_reason"], "OpenRouterError")

    def test_raises_when_fallback_is_disabled(self) -> None:
        def failed_transport(_: dict) -> dict:
            raise OpenRouterError("provider unavailable")

        chatbot = LLMChatbotOrchestrator(
            registry=FakeRegistry(),  # type: ignore[arg-type]
            config=config(fallback_to_rules=False),
            transport=failed_transport,
            fallback=FakeFallback(),  # type: ignore[arg-type]
        )

        with self.assertRaises(OpenRouterError):
            chatbot.process_message("Xin chào")


if __name__ == "__main__":
    unittest.main()
