from __future__ import annotations

import unittest

from chatbot_tools import build_default_registry
from chatbot_tools.retrieval import normalize_text


class KnowledgeToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = build_default_registry()

    def test_vietnamese_normalization(self) -> None:
        self.assertEqual(normalize_text("ĐeAdLiNe bao nhiêu z?"), "deadline bao nhieu z")

    def test_deadline_requires_all_required_slots(self) -> None:
        # When both assignment and module are None, should be ambiguous
        result = self.registry.execute(
            "lookup_deadline",
            {"assignment": None, "module": None, "cohort": "k3"},
        )
        self.assertEqual(result["status"], "ambiguous")
        self.assertIn("assignment", result["missing_fields"])
        self.assertEqual(result["citations"], [])

    def test_search_returns_results(self) -> None:
        result = self.registry.execute(
            "search_official_sources",
            {"query": "XP daily checkin", "category": None, "at": None, "limit": 5},
        )
        self.assertEqual(result["status"], "ok")
        self.assertGreater(len(result["data"]), 0)

    def test_unknown_arguments_are_rejected(self) -> None:
        result = self.registry.execute(
            "lookup_event",
            {"event_name": "demo_day", "cohort": "k3", "secret": "do-not-accept"},
        )
        self.assertEqual(result["status"], "rejected")

    def test_function_definitions_cover_all_tools(self) -> None:
        names = {definition["name"] for definition in self.registry.definitions()}
        self.assertEqual(
            names,
            {
                "lookup_deadline",
                "lookup_event",
                "lookup_gate",
                "lookup_exam_slot",
                "lookup_xp",
                "lookup_team_mentor",
                "lookup_slash_command",
                "search_official_sources",
                "offer_ticket",
                "create_ticket",
            },
        )

    def test_xp_tool(self) -> None:
        result = self.registry.execute(
            "lookup_xp",
            {"activity": "daily", "cohort": "k3", "at": None},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["xp"], 5)

    def test_slash_command_tool(self) -> None:
        result = self.registry.execute(
            "lookup_slash_command",
            {"command": "/daily"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("daily", result["data"]["command"])

    def test_gate_tool(self) -> None:
        result = self.registry.execute(
            "lookup_gate",
            {"gate_name": "cp3", "cohort": "k3", "at": None},
        )
        self.assertEqual(result["status"], "ok")

    def test_offer_and_create_ticket_tools(self) -> None:
        offer_res = self.registry.execute(
            "offer_ticket",
            {
                "category": "deadline",
                "question": "Hỏi deadline WA3",
                "known_context": {"assignment": "wa3"},
                "missing_information": [],
                "clarification_attempts": 2,
                "source_ids": [],
            },
        )
        self.assertEqual(offer_res["status"], "ok")
        self.assertEqual(offer_res["data"]["target_channel"], "assignment-support")

        req_id = offer_res["data"]["request_id"]
        create_res = self.registry.execute(
            "create_ticket",
            {
                "request_id": req_id,
                "user_consent": True,
            },
        )
        self.assertEqual(create_res["status"], "ok")
        self.assertTrue(create_res["data"]["sent"])


if __name__ == "__main__":
    unittest.main()
