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

    def test_search_respects_minimum_score(self) -> None:
        result = self.registry.execute(
            "search_official_sources",
            {
                "query": "deadline",
                "category": None,
                "at": None,
                "limit": 5,
                "min_score": 1000.0,
            },
        )
        self.assertEqual(result["status"], "not_found")

    def test_search_requires_named_resource_anchor(self) -> None:
        jira_result = self.registry.execute(
            "search_official_sources",
            {
                "query": "tìm bài setup jira",
                "category": "learning_material",
                "required_terms": ["jira"],
            },
        )
        self.assertEqual(jira_result["status"], "not_found")

        workshop_result = self.registry.execute(
            "search_official_sources",
            {
                "query": "tài liệu workshop 2",
                "category": "learning_material",
                "required_terms": ["workshop", "2"],
            },
        )
        self.assertEqual(workshop_result["status"], "ok")

    def test_curated_docs_knowledge_is_loaded(self) -> None:
        expected_ids = {
            "handbook_attendance_policy",
            "handbook_online_learning_policy",
            "handbook_laptop_requirements",
            "handbook_learning_platform",
            "docs_weekly_rhythm_k3",
            "docs_workshop_catalog_k3",
        }
        actual_ids = {
            record.source_id for record in self.registry.knowledge.store.records
        }
        self.assertTrue(expected_ids.issubset(actual_ids))

    def test_raw_discord_is_only_loaded_as_verified_canonical_facts(self) -> None:
        discord_records = [
            record
            for record in self.registry.knowledge.store.records
            if record.attributes.get("source_file") == "discord_messages.json"
        ]
        self.assertTrue(discord_records)
        for record in discord_records:
            self.assertEqual(
                record.attributes["verification_method"],
                "repeated_consensus",
            )
            self.assertNotIn("author", record.attributes)
            self.assertNotIn("https://discord.com/channels", record.text)

        source_files = {
            record.attributes.get("source_file")
            for record in self.registry.knowledge.store.records
        }
        self.assertNotIn("discord.har.json", source_files)

    def test_search_respects_category(self) -> None:
        result = self.registry.execute(
            "search_official_sources",
            {
                "query": "nghỉ tối đa mấy buổi",
                "category": "policy_attendance",
                "at": None,
                "limit": 5,
                "min_score": 0.0,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(
            all(item["category"] == "policy_attendance" for item in result["data"])
        )

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

    def test_gate_deadline_is_unsupported_when_source_only_has_requirements(self) -> None:
        result = self.registry.execute(
            "lookup_gate",
            {
                "gate_name": "cp3",
                "requested_fact": "deadline",
                "cohort": "k3",
                "at": None,
            },
        )

        self.assertEqual(result["status"], "unsupported")
        self.assertIsNone(result["data"])
        self.assertGreater(len(result["citations"]), 0)

    def test_k4_gate_uses_shared_k3_cohort_source(self) -> None:
        result = self.registry.execute(
            "lookup_gate",
            {"gate_name": "cp2", "cohort": "k4", "at": None},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["gate_name"], "cp2")
        self.assertEqual(result["data"]["cohort"], "k4")
        self.assertEqual(result["data"]["source_cohort"], "k3")
        self.assertTrue(result["data"]["cohort_alias_applied"])
        self.assertIn("Nguồn dùng chung K3→K4", result["citations"][0]["title"])

    def test_k4_deadline_uses_shared_k3_cohort_source(self) -> None:
        result = self.registry.execute(
            "lookup_deadline",
            {
                "assignment": "ai_log",
                "module": None,
                "cohort": "k4",
                "at": None,
            },
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["cohort"], "k4")
        self.assertEqual(result["data"]["source_cohort"], "k3")

    def test_demo_day_deadline_uses_event_date_not_deliverable_lists(self) -> None:
        result = self.registry.execute(
            "lookup_deadline",
            {
                "assignment": "demo_day",
                "module": None,
                "cohort": "k4",
                "at": "2026-07-31T15:54:00+07:00",
            },
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["deadline"], "2026-09-01")
        self.assertEqual(result["data"]["assignment"], "demo_day")
        self.assertEqual(result["data"]["cohort"], "k4")
        self.assertEqual(result["data"]["source_cohort"], "k3")
        self.assertEqual(
            result["citations"][0]["source_id"],
            "official_demo_day_k3",
        )

    def test_deliverable_list_difference_is_not_a_deadline_conflict(self) -> None:
        result = self.registry.execute(
            "lookup_deadline",
            {
                "assignment": "demo_day_deliverables",
                "module": None,
                "cohort": "k3",
                "at": "2026-07-31T15:54:00+07:00",
            },
        )

        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["conflicts"], [])

    def test_k4_alias_is_limited_to_configured_categories(self) -> None:
        result = self.registry.execute(
            "lookup_event",
            {"event_name": "demo_day", "cohort": "k4", "at": None},
        )
        self.assertEqual(result["status"], "not_found")

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

    def test_feature_5_sentiment_and_priority_ticket(self) -> None:
        # Test URGENT priority detection
        offer_res = self.registry.execute(
            "offer_ticket",
            {
                "category": "safety",
                "question": "Có bạn trong nhóm nhắn tin quấy rối em gấp lắm",
                "known_context": {},
                "missing_information": [],
                "clarification_attempts": 2,
                "source_ids": [],
            },
        )
        self.assertEqual(offer_res["status"], "ok")
        self.assertEqual(offer_res["data"]["priority"], "URGENT")
        self.assertEqual(offer_res["data"]["sentiment"], "stressed_or_urgent")


if __name__ == "__main__":
    unittest.main()
