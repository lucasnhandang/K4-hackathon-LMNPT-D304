"""Tests for the RAG response generator.

Uses mocked LLM client to avoid real API calls.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from chatbot_tools.llm_client import LLMClient, LLMResponse
from chatbot_tools.rag_generator import RAGGenerator


class RAGGeneratorTests(unittest.TestCase):
    """Test RAGGenerator with mocked LLM."""

    def setUp(self):
        self.mock_client = MagicMock(spec=LLMClient)
        self.mock_client.is_available.return_value = True
        self.generator = RAGGenerator(self.mock_client)

    def test_generate_with_context(self):
        """Test RAG generation with official source context."""
        self.mock_client.chat.return_value = LLMResponse(
            content="Deadline WA3 là ngày 15/08. Bạn nộp tại kênh #assignment.",
            model="test/model",
            usage={"total_tokens": 50},
            finish_reason="stop",
        )

        result = self.generator.generate(
            query="Deadline WA3 khi nào?",
            context_chunks=[
                {
                    "source_id": "src_001",
                    "category": "deadline",
                    "score": 0.85,
                    "attributes": {"assignment": "WA3", "deadline": "2025-08-15"},
                    "quote": "Weekly Assignment 3 deadline: 15/08/2025",
                }
            ],
        )

        self.assertIn("Deadline WA3", result["response"])
        self.assertTrue(result["grounded"])
        self.assertEqual(result["model"], "test/model")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["type"], "official")

    def test_generate_without_context(self):
        """Test RAG generation when no context is available."""
        self.mock_client.chat.return_value = LLMResponse(
            content="Mình chưa tìm thấy thông tin chính xác về câu hỏi này.",
            model="test/model",
            usage={},
            finish_reason="stop",
        )

        result = self.generator.generate(
            query="Python là gì?",
            context_chunks=[],
        )

        self.assertFalse(result["grounded"])
        self.assertEqual(len(result["sources"]), 0)

    def test_generate_with_community_matches(self):
        """Test RAG generation with community Q&A matches."""
        self.mock_client.chat.return_value = LLMResponse(
            content="Bạn có thể xem link này trong kênh cộng đồng.",
            model="test/model",
            usage={},
            finish_reason="stop",
        )

        result = self.generator.generate(
            query="Có ai biết link workshop không?",
            context_chunks=[],
            community_matches=[
                {
                    "question_preview": "Link workshop ở đâu?",
                    "jump_url": "https://discord.com/...",
                    "score": 0.75,
                }
            ],
        )

        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["type"], "community")

    def test_generate_llm_unavailable(self):
        """Test graceful fallback when LLM is not available."""
        self.mock_client.is_available.return_value = False

        result = self.generator.generate(query="Hello")

        self.assertIn("thử lại sau", result["response"])
        self.assertEqual(result["model"], "none")
        self.assertFalse(result["grounded"])

    def test_generate_llm_error(self):
        """Test graceful fallback when LLM call fails."""
        self.mock_client.chat.side_effect = Exception("API error")

        result = self.generator.generate(query="Hello")

        self.assertIn("lỗi", result["response"])
        self.assertEqual(result["model"], "error")
        self.assertFalse(result["grounded"])

    def test_system_prompt_includes_rules(self):
        """Test that system prompt contains grounding rules."""
        from chatbot_tools.rag_generator import SYSTEM_PROMPT

        self.assertIn("CHỈ dùng thông tin", SYSTEM_PROMPT)
        self.assertIn("KHÔNG tự tạo thông tin", SYSTEM_PROMPT)
        self.assertIn("trích dẫn nguồn", SYSTEM_PROMPT)

    def test_context_building(self):
        """Test context string construction."""
        context = self.generator._build_context(
            context_chunks=[
                {
                    "source_id": "src_001",
                    "category": "deadline",
                    "score": 0.9,
                    "attributes": {"assignment": "WA3"},
                    "quote": "Deadline WA3",
                },
                {
                    "source_id": "src_002",
                    "category": "deadline",
                    "score": 0.7,
                    "attributes": {},
                    "quote": "",
                },
            ],
            community_matches=[
                {
                    "question_preview": "Deadline WA3?",
                    "jump_url": "https://discord.com/...",
                    "score": 0.6,
                }
            ],
        )

        self.assertIn("NGUỒN CHÍNH THỨC", context)
        self.assertIn("src_001", context)
        self.assertIn("HỘI THOẠI CỘNG ĐỒNG", context)
        self.assertIn("Deadline WA3?", context)

    def test_context_truncation(self):
        """Test that very long context is truncated."""
        long_chunks = [
            {
                "source_id": f"src_{i:03d}",
                "category": "test",
                "score": 0.5,
                "attributes": {"data": "x" * 500},
                "quote": "y" * 500,
            }
            for i in range(20)
        ]

        context = self.generator._build_context(long_chunks, None)
        self.assertLessEqual(len(context), 3500)  # MAX_CONTEXT_CHARS + margin

    def test_user_message_building(self):
        """Test user message construction."""
        message = self.generator._build_user_message(
            query="Deadline WA3?",
            context="[CONTEXT]\nTest context\n[/CONTEXT]",
            intent="ask_deadline",
            extra_instructions="Be concise",
        )

        self.assertIn("ask_deadline", message)
        self.assertIn("[CONTEXT]", message)
        self.assertIn("Deadline WA3?", message)
        self.assertIn("Be concise", message)

    def test_sources_collection(self):
        """Test source reference collection."""
        sources = self.generator._collect_sources(
            context_chunks=[
                {"source_id": "src_001", "category": "deadline"},
                {"source_id": "src_002", "category": "event"},
            ],
            community_matches=[
                {"question_preview": "Test?", "jump_url": "https://..."},
            ],
        )

        self.assertEqual(len(sources), 3)
        self.assertEqual(sources[0]["type"], "official")
        self.assertEqual(sources[2]["type"], "community")


if __name__ == "__main__":
    unittest.main()
