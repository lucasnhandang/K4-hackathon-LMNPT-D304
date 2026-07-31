#!/usr/bin/env python3
"""Build official knowledge records from the curated JSON files in docs/.

The raw Discord export and HAR file are deliberately excluded: they contain
user data and unverified bot answers, so they are not authoritative sources.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = (
    ROOT / "codebase" / "backend" / "chatbot_tools" / "data" / "official_sources.json"
)
COHORT_SOURCE = ROOT / "docs" / "tong_hop_du_lieu_AI20K_Cohort_III.json"
HANDBOOK_SOURCE = ROOT / "docs" / "tong_hop_so_tay_hoc_vien_AI_thuc_chien.json"
DISCORD_SOURCE = ROOT / "docs" / "discord_messages.json"
UPDATED_AT = "2026-07-31T00:00:00+07:00"
KUTEBOT_ID = "1480861618358452417"

# Hand-authored fixture records (no source_file attribute — predate the docs
# ingestion pipeline) that are now factually superseded by a verified record
# derived from the real curated docs, and that genuinely conflict with it
# (not just a differing "event_name"/"assignment" label — an actual
# disagreement on the fact itself). Kept out of the output so
# _find_conflicts() doesn't force every "demo day deadline" question into an
# ESCALATE. See DECISIONS.md D-011 for how this was found and verified.
RETIRED_FIXTURE_SOURCE_IDS = {
    # Listed generic/English deliverables (business_model_canvas,
    # competitive_analysis, user_persona, ...) that don't appear anywhere in
    # the real source; docs_demo_day_deliverables_k3 (from
    # quality_control_and_demo_day.mandatory_deliverables in COHORT_SOURCE)
    # is the verified replacement.
    "official_deliverables_k3",
}


def _record(
    source_id: str,
    *,
    title: str,
    locator: str,
    category: str,
    text: str,
    attributes: dict[str, Any],
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "locator": locator,
        "category": category,
        "text": text,
        "updated_at": UPDATED_AT,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "attributes": attributes,
        "official": True,
    }


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(_as_text(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_as_text(item)}" for key, item in value.items())
    return str(value)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", value)


def _discord_pairs(payload: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    messages = payload["messages"]
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, question in enumerate(messages[:-1]):
        if question.get("author", {}).get("id") == KUTEBOT_ID:
            continue
        answer = messages[index + 1]
        if answer.get("author", {}).get("id") == KUTEBOT_ID:
            pairs.append((question, answer))
    return pairs


def _evidence(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    question_any: tuple[str, ...],
    answer_all: tuple[str, ...],
    minimum: int = 2,
) -> list[str]:
    matches: list[str] = []
    for question, answer in pairs:
        question_text = _normalize(question.get("content", ""))
        answer_text = _normalize(answer.get("content", ""))
        if not any(_normalize(term) in question_text for term in question_any):
            continue
        if not all(_normalize(term) in answer_text for term in answer_all):
            continue
        matches.extend([question["id"], answer["id"]])
    if len(matches) // 2 < minimum:
        return []
    return matches


def extract_discord_facts(payload: dict[str, Any]) -> dict[str, list[str]]:
    """Return only repeated, internally consistent facts from historical Q&A."""
    pairs = _discord_pairs(payload)
    return {
        "mentoring_schedule": _evidence(
            pairs,
            question_any=("mentor duty", "mentoring duty", "lịch trình tuần", "lịch trình cả tuần"),
            answer_all=("20:00", "22:00", "thứ 4", "thứ 7"),
        ),
        "weekly_deadline": _evidence(
            pairs,
            question_any=("khi nao nop weekly", "hạn update weekly", "deadline weekly"),
            answer_all=("12h00", "mentor duty"),
        ),
        "rank_command": _evidence(
            pairs,
            question_any=("xem xp", "tổng điểm kinh nghiệm", "điểm xp của mình"),
            answer_all=("/rank", "xp"),
        ),
        "topic_availability": _evidence(
            pairs,
            question_any=("đề tài này đã có", "đề tài nào còn", "kiểm tra đề tài"),
            answer_all=("/exam available", "2 team"),
        ),
        "team_change_ticket": _evidence(
            pairs,
            question_any=("đổi đề tài", "doi de", "join vào nhóm khác"),
            answer_all=("ticket",),
        ),
        "gate_1": _evidence(
            pairs,
            question_any=("gate 1 là bao giờ", "khi nao nop gate 1", "gate 1 nộp"),
            answer_all=("2/8/2026", "brief", "prd", "wireframe", "ai log"),
        ),
        "event_announcement_channel": _evidence(
            pairs,
            question_any=("lịch trình tuần", "lịch trình cả tuần", "sự kiện gì"),
            answer_all=("thông-báo",),
        ),
    }


def apply_discord_enrichment(
    records: list[dict[str, Any]],
    facts: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Merge canonical facts into curated records; never copy raw bot prose."""
    by_id = {record["source_id"]: record for record in records}

    def enrich(source_id: str, text: str, fact_name: str, **attributes: Any) -> None:
        evidence_ids = facts.get(fact_name, [])
        if not evidence_ids:
            return
        record = by_id[source_id]
        record["text"] = f"{record['text']} {text}".strip()
        record["attributes"].update(attributes)
        record["attributes"]["discord_verification"] = {
            "method": "repeated_consensus",
            "fact": fact_name,
            "evidence_message_ids": evidence_ids,
            "source_file": DISCORD_SOURCE.name,
        }

    enrich(
        "docs_mentoring_duty_rhythm_k3",
        "Khung giờ được lặp lại nhất quán trong lịch sử Q&A là 20:00–22:00.",
        "mentoring_schedule",
        start_time="20:00",
        end_time="22:00",
    )
    enrich(
        "docs_weekly_rhythm_k3",
        "Mentoring Duty diễn ra 20:00–22:00; lịch cập nhật được theo dõi tại kênh #thông-báo.",
        "mentoring_schedule",
        mentoring_time="20:00-22:00",
    )
    enrich(
        "docs_weekly_report_k3",
        "Lịch sử Q&A thống nhất hạn nộp là 12h00 trưa trước buổi Mentoring Duty.",
        "weekly_deadline",
        cutoff_time="12:00",
    )

    discord_records: list[dict[str, Any]] = []
    provenance = {
        "cohort": "k3",
        "source_file": DISCORD_SOURCE.name,
        "verification_method": "repeated_consensus",
    }
    if facts.get("rank_command"):
        discord_records.append(
            _record(
                "discord_verified_rank_xp_k3",
                title="Tra cứu XP bằng lệnh /rank",
                locator="Discord historical Q&A / repeated consensus",
                category="xp",
                text="Dùng lệnh /rank để xem lịch sử XP và điểm kinh nghiệm hiện có.",
                attributes={
                    "activity": "rank",
                    "command": "/rank",
                    "evidence_message_ids": facts["rank_command"],
                    **provenance,
                },
            )
        )
    if facts.get("topic_availability"):
        discord_records.append(
            _record(
                "discord_verified_topic_availability_k3",
                title="Kiểm tra đề tài còn trống",
                locator="Discord historical Q&A / repeated consensus",
                category="topic_availability",
                text=(
                    "Dùng /exam available để xem mã đề còn trống; mỗi đề tài có tối đa "
                    "2 team cùng chọn."
                ),
                attributes={
                    "topic": "topic_availability",
                    "command": "/exam available",
                    "evidence_message_ids": facts["topic_availability"],
                    **provenance,
                },
            )
        )
    if facts.get("team_change_ticket"):
        discord_records.append(
            _record(
                "discord_verified_team_change_k3",
                title="Yêu cầu đổi nhóm hoặc đổi đề tài",
                locator="Discord historical Q&A / repeated consensus",
                category="team_change",
                text=(
                    "Khi cần đổi nhóm hoặc đổi đề tài, tạo ticket để Mod xử lý trước "
                    "thời hạn; hệ thống không tự đổi."
                ),
                attributes={
                    "topic": "team_change",
                    "command": "/ticket create",
                    "evidence_message_ids": facts["team_change_ticket"],
                    **provenance,
                },
            )
        )
    if facts.get("gate_1"):
        discord_records.append(
            _record(
                "official_gate_cp1_k3",
                title="Gate 1 — Chốt đề tài",
                locator="Discord historical Q&A / repeated consensus",
                category="gate",
                text=(
                    "Gate 1 (CP1) chốt đề tài, deadline 23:59 ngày 02/08/2026. "
                    "Deliverables gồm Brief, PRD, Wireframe/UI Flow, GitHub Repo Setup "
                    "và AI Log; nộp một link chứa đủ deliverables."
                ),
                attributes={
                    "gate_name": "cp1",
                    "deadline": "2026-08-02T23:59:00+07:00",
                    "requirements": [
                        "brief",
                        "prd",
                        "wireframe_ui_flow",
                        "github_repo_setup",
                        "ai_log",
                    ],
                    "evidence_message_ids": facts["gate_1"],
                    **provenance,
                },
                valid_to="2026-08-02T23:59:00+07:00",
            )
        )
    return records + discord_records


# FAQ ids already covered by their own dedicated record (laptop=8, opportunities=15,
# leave-request procedure=5 duplicates attendance_policy.procedure). The rest had no
# record at all before this pass — see D-010.
_FAQ_IDS_ALREADY_COVERED = {5, 8, 15}


def _build_faq_records(handbook: dict[str, Any], provenance: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for item in handbook["faq"]:
        if item["id"] in _FAQ_IDS_ALREADY_COVERED:
            continue
        answer_text = _as_text(item["answer"])
        records.append(
            _record(
                f"handbook_faq_{item['id']}",
                title=f"FAQ #{item['id']} — {item['question']}",
                locator=f"Sổ tay học viên / FAQ {item['id']}",
                category="faq",
                text=f"{item['question']} {answer_text}",
                attributes={
                    "topic": "faq",
                    "faq_id": item["id"],
                    "question": item["question"],
                    "answer": item["answer"],
                    **provenance,
                },
            )
        )
    return records


def build_handbook_records(handbook: dict[str, Any]) -> list[dict[str, Any]]:
    attendance = handbook["attendance_policy"]
    laptop = next(item for item in handbook["faq"] if item["id"] == 8)["answer"]
    learning_platform = handbook["learning_platform"]
    reservation = handbook["reservation_policy"]
    completion = handbook["completion_requirements"]
    allowance = handbook["tuition_and_allowance"]
    opportunities = next(item for item in handbook["faq"] if item["id"] == 15)["answer"]
    overview = handbook["overview"]
    internship = handbook["internship"]
    schedule = handbook["schedule"]
    facilities = handbook["facilities"]
    contact = handbook["contact"]

    provenance = {
        "source_file": HANDBOOK_SOURCE.name,
        "source_version": handbook["metadata"]["version"],
    }
    records = [
        _record(
            "handbook_attendance_policy",
            title="Quy định chuyên cần và xin nghỉ",
            locator="Sổ tay học viên / attendance_policy",
            category="policy_attendance",
            text=(
                f"Học viên được nghỉ tối đa {attendance['maximum_absence_sessions']} buổi. "
                f"{_as_text(attendance['restrictions'])}. "
                f"Quy trình xin nghỉ: {_as_text(attendance['procedure'])}."
            ),
            attributes={
                "topic": "attendance",
                "maximum_absence_sessions": attendance["maximum_absence_sessions"],
                "restrictions": attendance["restrictions"],
                "procedure": attendance["procedure"],
                **provenance,
            },
        ),
        _record(
            "handbook_online_learning_policy",
            title="Hình thức học và chính sách học online",
            locator="Sổ tay học viên / attendance_policy.online_policy; FAQ 3",
            category="policy_online",
            text=(
                "Chương trình học trực tiếp theo kế hoạch của Ban Tổ chức. "
                f"{attendance['online_policy']}"
            ),
            attributes={
                "topic": "online_learning",
                "study_mode": handbook["overview"]["study_mode"],
                "online_policy": attendance["online_policy"],
                **provenance,
            },
        ),
        _record(
            "handbook_laptop_requirements",
            title="Cấu hình laptop tối thiểu",
            locator="Sổ tay học viên / FAQ 8",
            category="policy_laptop",
            text=(
                "Laptop cần CPU Intel Core i7, Apple M2 hoặc tương đương; "
                "RAM tối thiểu 16GB; ít nhất 256GB SSD; hỗ trợ Windows 10/11, "
                "macOS hoặc Linux; kết nối mạng ổn định."
            ),
            attributes={"topic": "laptop_requirements", **laptop, **provenance},
        ),
        _record(
            "handbook_learning_platform",
            title="Nền tảng học tập LearnWorlds",
            locator="Sổ tay học viên / learning_platform",
            category="learning_material",
            text=(
                f"Sử dụng {learning_platform['name']} để "
                f"{_as_text(learning_platform['uses'])}."
            ),
            attributes={
                "topic": "learning_platform",
                "platform": learning_platform["name"],
                "uses": learning_platform["uses"],
                **provenance,
            },
        ),
        _record(
            "handbook_submission_platform",
            title="Nền tảng nộp bài LearnWorlds",
            locator="Sổ tay học viên / learning_platform",
            category="submission_channel",
            text=(
                "Bài học và bài tập của chương trình được truy cập, nộp bài và nhận "
                f"phản hồi trên {learning_platform['name']}."
            ),
            attributes={
                "topic": "assignment_submission",
                "platform": learning_platform["name"],
                "uses": learning_platform["uses"],
                **provenance,
            },
        ),
        _record(
            "handbook_reservation_policy",
            title="Quy định bảo lưu",
            locator="Sổ tay học viên / reservation_policy",
            category="policy",
            text=(
                f"{reservation['general_rule']} Ngoại lệ: "
                f"{_as_text(reservation['exceptions'])}. Yêu cầu: "
                f"{_as_text(reservation['requirements'])}."
            ),
            attributes={"topic": "reservation", **reservation, **provenance},
        ),
        _record(
            "handbook_completion_requirements",
            title="Điều kiện hoàn thành chương trình",
            locator="Sổ tay học viên / completion_requirements",
            category="policy",
            text=(
                f"Điều kiện đạt: {_as_text(completion['pass_conditions'])}. "
                f"Điều kiện không đạt: {_as_text(completion['fail_conditions'])}."
            ),
            attributes={"topic": "completion", **completion, **provenance},
        ),
        _record(
            "handbook_tuition_allowance",
            title="Học phí, trợ cấp và điều kiện",
            locator="Sổ tay học viên / tuition_and_allowance",
            category="policy",
            text=(
                f"Chương trình tài trợ {allowance['tuition_support_percent']}% học phí "
                f"và trợ cấp {allowance['monthly_allowance_vnd']:,} đồng/tháng nếu "
                f"đáp ứng điều kiện: {_as_text(allowance['conditions'])}."
            ),
            attributes={"topic": "tuition_allowance", **allowance, **provenance},
        ),
        _record(
            "handbook_post_program_opportunities",
            title="Cơ hội sau chương trình",
            locator="Sổ tay học viên / FAQ 15",
            category="career",
            text=f"Cơ hội sau chương trình: {_as_text(opportunities)}.",
            attributes={"topic": "post_program_opportunities", **provenance},
        ),
        _record(
            "handbook_program_highlights",
            title="Điểm nổi bật của chương trình",
            locator="Sổ tay học viên / highlights",
            category="program_overview",
            text=_as_text(handbook["highlights"]),
            attributes={"topic": "program_highlights", "highlights": handbook["highlights"], **provenance},
        ),
        _record(
            "handbook_program_structure",
            title="Cấu trúc 3 giai đoạn của chương trình",
            locator="Sổ tay học viên / program_structure",
            category="program_overview",
            text="; ".join(
                f"Giai đoạn {stage['stage']} — {stage['name']} ({stage['duration_weeks']} tuần)"
                + (f", track: {_as_text(stage['tracks'])}" if "tracks" in stage else "")
                for stage in handbook["program_structure"]
            ),
            attributes={
                "topic": "program_structure",
                "duration_weeks_total": overview["duration_weeks"],
                "stages": handbook["program_structure"],
                **provenance,
            },
        ),
        _record(
            "handbook_internship",
            title="Thực tập tại doanh nghiệp đối tác",
            locator="Sổ tay học viên / internship",
            category="internship",
            text=(
                f"Thực tập giai đoạn 3 tại các doanh nghiệp: {_as_text(internship['companies'])}. "
                f"Phân bổ dựa trên: {_as_text(internship['allocation_basis'])}. "
                f"Địa điểm: {_as_text(internship['locations'])}. "
                f"Ưu tiên Cohort 1: {internship['cohort_1_priority']}."
            ),
            attributes={"topic": "internship", **internship, **provenance},
        ),
        _record(
            "handbook_daily_schedule",
            title="Lịch học hàng ngày theo từng giai đoạn",
            locator="Sổ tay học viên / schedule",
            category="policy",
            text=(
                f"Giai đoạn 1 — sáng: {schedule['stage_1']['morning']}; "
                f"chiều: {schedule['stage_1']['afternoon']}; "
                f"tối/cuối tuần: {schedule['stage_1']['evening_weekend']}. "
                f"Giai đoạn 2 — sáng: {schedule['stage_2']['morning']}; "
                f"chiều/tối/cuối tuần: {schedule['stage_2']['afternoon_evening_weekend']}. "
                f"Giai đoạn 3: {schedule['stage_3']}."
            ),
            attributes={"topic": "daily_schedule", "schedule": schedule, **provenance},
        ),
        _record(
            "handbook_evaluation_criteria",
            title="Tiêu chí đánh giá kết quả học tập",
            locator="Sổ tay học viên / evaluation",
            category="policy",
            text="Học viên được đánh giá qua: " + _as_text(handbook["evaluation"]) + ".",
            attributes={"topic": "evaluation", "criteria": handbook["evaluation"], **provenance},
        ),
        _record(
            "handbook_facilities",
            title="Cơ sở vật chất và tiện ích tại VinUni",
            locator="Sổ tay học viên / facilities",
            category="learning_material",
            text=(
                "Phòng học: " + "; ".join(
                    f"{room['name']} (sức chứa {room['capacity']})" for room in facilities["classrooms"]
                )
                + ". Tiện ích: " + _as_text(facilities["services"]) + "."
            ),
            attributes={"topic": "facilities", **facilities, **provenance},
        ),
        _record(
            "handbook_contact_support",
            title="Kênh liên hệ hỗ trợ chương trình",
            locator="Sổ tay học viên / contact",
            category="contact",
            text=(
                f"Email chương trình: {contact['email']}. Điện thoại: {contact['phone']} "
                f"(số nội bộ hỗ trợ kỹ thuật: {contact['technical_support_extension']}). "
                f"Địa chỉ: {contact['address']}. Website: {contact['website']}. "
                f"Đầu mối hỗ trợ học viên: {contact['student_support']['name']} — "
                f"{contact['student_support']['role']}, {contact['student_support']['office']}."
            ),
            # Deliberately omit contact["leaders"] (named individuals' personal emails):
            # this bot is public on the internet (see DECISIONS.md D-008) — surfacing
            # named staff's direct email on request turns a handbook page into an
            # instant lookup tool for anyone, not just enrolled students. Point people
            # at the general program contact / student_support channel instead.
            attributes={
                "topic": "contact",
                "email": contact["email"],
                "phone": contact["phone"],
                "technical_support_extension": contact["technical_support_extension"],
                "address": contact["address"],
                "website": contact["website"],
                "student_support": contact["student_support"],
                **provenance,
            },
        ),
    ]
    records.extend(_build_faq_records(handbook, provenance))
    return records


def build_cohort_records(cohort: dict[str, Any]) -> list[dict[str, Any]]:
    rhythm = cohort["weekly_operating_rhythm"]["base_schedule"]
    activities = {item["activity"]: item for item in rhythm}
    team = cohort["team_formation_and_topic_selection"]
    weekly = cohort["weekly_program"]
    xp_rules = cohort["xp_system"]["earning_rules"]
    xp_by_activity = {item["activity"]: item for item in xp_rules}
    commands = cohort["discord_commands"]
    overview = cohort["program_overview"]
    source_file = COHORT_SOURCE.name
    provenance = {"cohort": "k3", "source_file": source_file}
    valid_from = f"{overview['calendar_coverage']['start']}T00:00:00+07:00"
    valid_to = f"{overview['calendar_coverage']['end']}T23:59:59+07:00"

    records = [
        _record(
            "docs_weekly_rhythm_k3",
            title="Nhịp vận hành hàng tuần — AI20K Cohort III",
            locator="Tổng quan Cohort III / weekly_operating_rhythm",
            category="event",
            text=(
                "Lịch cơ bản: Workshop tối Thứ 5 và Chủ Nhật, thường 2 buổi/tuần; "
                "Office Hours tối Thứ 2 và Thứ 6, thường 2 buổi/tuần; "
                "Mentoring Duty tối Thứ 4 và Thứ 7, 2 buổi/tuần để theo dõi tiến độ, "
                "chấm điểm và gỡ khó. Lịch có thể được BTC cập nhật theo thông báo chính thức."
            ),
            attributes={"event_name": "weekly_rhythm", "activities": rhythm, **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_workshop_rhythm_k3",
            title="Lịch Workshop hàng tuần — AI20K Cohort III",
            locator="Tổng quan Cohort III / weekly_operating_rhythm / Workshop",
            category="event",
            text=(
                f"Workshop diễn ra {activities['Workshop']['frequency']}, "
                f"thường vào {activities['Workshop']['usual_time']}. "
                "Lịch cụ thể có thể được BTC cập nhật theo thông báo chính thức."
            ),
            attributes={"event_name": "workshop", **activities["Workshop"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_office_hours_rhythm_k3",
            title="Lịch Office Hours hàng tuần — AI20K Cohort III",
            locator="Tổng quan Cohort III / weekly_operating_rhythm / Office Hours",
            category="event",
            text=(
                f"Office Hours diễn ra {activities['Office Hours']['frequency']}, "
                f"thường vào {activities['Office Hours']['usual_time']}."
            ),
            attributes={"event_name": "office hour", **activities["Office Hours"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_mentoring_duty_rhythm_k3",
            title="Lịch Mentoring Duty hàng tuần — AI20K Cohort III",
            locator="Tổng quan Cohort III / weekly_operating_rhythm / Mentoring Duty",
            category="event",
            text=(
                f"Mentoring Duty diễn ra {activities['Mentoring Duty']['frequency']}, "
                f"thường vào {activities['Mentoring Duty']['usual_time']}; mục đích: "
                f"{_as_text(activities['Mentoring Duty']['purposes'])}."
            ),
            attributes={
                "event_name": "mentoring",
                **activities["Mentoring Duty"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_team_topic_selection_k3",
            title="Ghép team và chọn đề tài — AI20K Cohort III",
            locator="Tổng quan Cohort III / team_formation_and_topic_selection",
            category="topic_availability",
            text=(
                f"{_as_text(team['team_process'])}. "
                "Dùng /exam available để xem các mã đề còn trống; mỗi đề tài có tối đa 2 team."
            ),
            attributes={"topic": "team_topic_selection", "rules": team["team_process"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "official_team_naming_k3",
            title="Quy tắc đặt tên team — AI20K Cohort III",
            locator="Tổng quan Cohort III / naming_conventions",
            category="team_naming",
            text=(
                "Quy ước đặt tên: GitHub repository P-XXX; kênh Discord t-XXX; "
                "deploy URL c3-app-XXX; tên Zoom G-YY - TXXX - Họ và tên."
            ),
            attributes={
                "topic": "team_naming",
                "naming_convention": team["naming_conventions"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_weekly_report_k3",
            title="Quy định Weekly Report trước Mentoring Duty",
            locator="Tổng quan Cohort III / weekly_program / coaching_breakout_room",
            category="deadline",
            text=(
                f"{weekly['coaching_breakout_room']['weekly_report_rule']}. "
                "Dùng lệnh /weekly submit để nộp báo cáo tuần."
            ),
            attributes={"assignment": "weekly_report", **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_weekly_report_submission_k3",
            title="Nộp báo cáo tuần cho Mentoring Duty",
            locator="Tổng quan Cohort III / weekly_program / coaching_breakout_room",
            category="submission_channel",
            text=(
                "Báo cáo tuần cho buổi Mentoring Duty được nộp bằng lệnh "
                "/weekly submit; mỗi team nộp trước mỗi buổi Coaching."
            ),
            attributes={
                "topic": "weekly_report_submission",
                "command": "/weekly submit",
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "official_xp_daily_k3",
            title="Quy định XP — Daily stand-up",
            locator="Tổng quan Cohort III / xp_system / /daily",
            category="xp",
            text="/daily dùng để nộp daily stand-up và nhận 5 XP cho mỗi thành viên mỗi lần nộp.",
            attributes={**xp_by_activity["/daily"], "activity": "daily", **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "official_xp_weekly_k3",
            title="Quy định XP — Weekly report",
            locator="Tổng quan Cohort III / xp_system / /weekly submit",
            category="xp",
            text="/weekly submit dùng để nộp báo cáo tuần và nhận 10 XP cho mỗi thành viên.",
            attributes={
                **xp_by_activity["/weekly submit"],
                "activity": "weekly",
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "official_xp_gate_k3",
            title="Quy định XP — Gate",
            locator="Tổng quan Cohort III / xp_system / /gate submit",
            category="xp",
            text="/gate submit dùng để nộp gate cho team; mỗi gate được cộng 100 XP.",
            attributes={**xp_by_activity["/gate submit"], "activity": "gate", **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_xp_workshop_k3",
            title="Quy định XP — Tham gia Workshop",
            locator="Tổng quan Cohort III / xp_system / Workshop",
            category="xp",
            text="Tham gia Workshop được cộng 30 XP mỗi buổi.",
            attributes={
                **xp_by_activity["Tham gia Workshop"],
                "activity": "workshop",
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_workshop_catalog_k3",
            title="Danh mục 14 Workshop — AI20K Cohort III",
            locator="Tổng quan Cohort III / workshop_schedule",
            category="learning_material",
            text="; ".join(
                f"Workshop {item['order']}: {item['title']}"
                + (f" — {item['content']}" if item["content"] else "")
                for item in cohort["workshop_schedule"]
            ),
            attributes={
                "topic": "workshop_catalog",
                "workshops": cohort["workshop_schedule"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_ai_log_setup_k3",
            title="Hướng dẫn Setup AI Log",
            locator="Tổng quan Cohort III / ai_log",
            category="learning_material",
            text=(
                f"{cohort['ai_log']['definition']} {cohort['ai_log']['requirement']} "
                f"{cohort['ai_log']['instruction']}"
            ),
            attributes={"topic": "ai_log", **cohort["ai_log"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_demo_day_deliverables_k3",
            title="10 deliverable bắt buộc cho Demo Day",
            locator="Tổng quan Cohort III / quality_control_and_demo_day",
            category="deadline",
            text=(
                "10 deliverable bắt buộc: "
                f"{_as_text(cohort['quality_control_and_demo_day']['mandatory_deliverables'])}."
            ),
            attributes={
                "assignment": "demo_day_deliverables",
                "items": cohort["quality_control_and_demo_day"]["mandatory_deliverables"],
                "count": len(cohort["quality_control_and_demo_day"]["mandatory_deliverables"]),
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_master_timeline_k3",
            title="Master Timeline 6 tuần — AI20K Cohort III",
            locator="Tổng quan Cohort III / master_timeline",
            category="event",
            text="; ".join(
                f"Tuần {item['week']}"
                + (f" ({item['date']})" if item["date"] else "")
                + f": {item['milestone']}"
                + (f" — {item['gate']}" if item["gate"] else "")
                for item in cohort["master_timeline"]
            )
            + f" Lưu ý: {cohort['timeline_guidance']}",
            attributes={
                "event_name": "master_timeline",
                "milestones": cohort["master_timeline"],
                "guidance": cohort["timeline_guidance"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_schedule_change_week4_k3",
            title="Thay đổi lịch vận hành từ tuần 4",
            locator="Tổng quan Cohort III / weekly_operating_rhythm / from_week_4",
            category="event",
            text="Từ tuần 4: " + _as_text(cohort["weekly_operating_rhythm"]["from_week_4"]) + ".",
            attributes={
                "event_name": "schedule_change_week4",
                "changes": cohort["weekly_operating_rhythm"]["from_week_4"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_xp_levels_k3",
            title="Mốc XP để lên level (LV1–LV4)",
            locator="Tổng quan Cohort III / xp_system / levels",
            category="xp",
            text="; ".join(
                f"{lvl['level']} ({lvl['name']}): từ {lvl['required_xp']} XP"
                for lvl in cohort["xp_system"]["levels"]
            ),
            attributes={"topic": "xp_levels", "levels": cohort["xp_system"]["levels"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_xp_extra_activities_k3",
            title="Quy định XP — hỗ trợ cộng đồng và showcase",
            locator="Tổng quan Cohort III / xp_system / earning_rules",
            category="xp",
            text=(
                "Hỗ trợ cộng đồng được cộng 5–20 XP mỗi lần (tùy mức đóng góp). "
                "Showcase và feedback sản phẩm có thể được cộng XP thưởng thêm (không cố định)."
            ),
            attributes={
                "activity": "community_support_and_showcase",
                "community_support_xp_range": xp_by_activity["Hỗ trợ cộng đồng"]["xp_range"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_gate_definition_k3",
            title="Gate là gì & tiêu chí chấm điểm",
            locator="Tổng quan Cohort III / quality_control_and_demo_day / gates",
            category="gate",
            text=(
                f"{cohort['quality_control_and_demo_day']['gates']['definition']} "
                f"{cohort['quality_control_and_demo_day']['gates']['support']} "
                "Tiêu chí chấm điểm: "
                + _as_text(cohort["quality_control_and_demo_day"]["scoring_rubric"])
                + "."
            ),
            attributes={
                "topic": "gate_definition",
                "scoring_rubric": cohort["quality_control_and_demo_day"]["scoring_rubric"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_exam_bank_k3",
            title="Ngân hàng đề thi — nguyên tắc chọn đề",
            locator="Tổng quan Cohort III / exam_bank",
            category="exam_slot",
            text=(
                f"{cohort['exam_bank']['resource_label']}. Nguyên tắc cốt lõi: "
                f"{cohort['exam_bank']['core_principle']} — {cohort['exam_bank']['principle_explanation']}"
            ),
            attributes={"topic": "exam_bank", **cohort["exam_bank"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_support_automation_k3",
            title="Hệ thống hỗ trợ tự động và Trợ lý Kute",
            locator="Tổng quan Cohort III / support_and_automation",
            category="learning_material",
            text=(
                "Hệ thống tự động: " + _as_text(cohort["support_and_automation"]["server_system"]["functions"])
                + ". Trợ lý Kute (" + cohort["support_and_automation"]["kutebot"]["mention"] + "): "
                + _as_text(cohort["support_and_automation"]["kutebot"]["functions"]) + "."
            ),
            attributes={"topic": "support_and_automation", **cohort["support_and_automation"], **provenance},
            valid_from=valid_from,
            valid_to=valid_to,
        ),
        _record(
            "docs_supplementary_workshops_k3",
            title="Workshop bổ sung",
            locator="Tổng quan Cohort III / supplementary_workshop_topics",
            category="learning_material",
            text="Workshop bổ sung (ngoài 14 buổi chính): " + _as_text(cohort["supplementary_workshop_topics"]) + ".",
            attributes={
                "topic": "supplementary_workshops",
                "topics": cohort["supplementary_workshop_topics"],
                **provenance,
            },
            valid_from=valid_from,
            valid_to=valid_to,
        ),
    ]

    command_groups = ("reports", "exam", "personal_and_team", "gate", "ticket")
    canonical_command_ids = {
        "/daily": "official_command_daily_k3",
        "/rank": "official_command_rank_k3",
    }
    for group in command_groups:
        for item in commands[group]:
            command_id = item["command"].strip("/").replace(" ", "_")
            records.append(
                _record(
                    canonical_command_ids.get(
                        item["command"],
                        f"docs_command_{command_id}_k3",
                    ),
                    title=f"Hướng dẫn lệnh Discord — {item['command']}",
                    locator=f"Tổng quan Cohort III / discord_commands / {group}",
                    category="slash_command",
                    text=f"{item['command']}: {item['description']}.",
                    attributes={**item, **provenance},
                    valid_from=valid_from,
                    valid_to=valid_to,
                )
            )
    return records


def build(output: Path) -> tuple[int, int]:
    with COHORT_SOURCE.open(encoding="utf-8") as handle:
        cohort = json.load(handle)
    with HANDBOOK_SOURCE.open(encoding="utf-8") as handle:
        handbook = json.load(handle)
    with DISCORD_SOURCE.open(encoding="utf-8") as handle:
        discord = json.load(handle)
    with output.open(encoding="utf-8") as handle:
        current = json.load(handle)

    generated = build_handbook_records(handbook) + build_cohort_records(cohort)
    generated = apply_discord_enrichment(generated, extract_discord_facts(discord))
    generated_by_id = {record["source_id"]: record for record in generated}
    if len(generated_by_id) != len(generated):
        raise ValueError("Generated source_id values must be unique")

    managed_files = {COHORT_SOURCE.name, HANDBOOK_SOURCE.name, DISCORD_SOURCE.name}
    kept = [
        record
        for record in current["records"]
        if record["source_id"] not in generated_by_id
        and record.get("attributes", {}).get("source_file") not in managed_files
        and record["source_id"] not in RETIRED_FIXTURE_SOURCE_IDS
    ]
    records = kept + generated
    if len({record["source_id"] for record in records}) != len(records):
        raise ValueError("Final source_id values must be unique")

    payload = {
        "fixture_notice": (
            "Knowledge tổng hợp từ fixture, JSON đã kiểm duyệt và các fact Discord "
            "đạt repeated-consensus. Raw Discord/HAR không được nhập trực tiếp."
        ),
        "records": records,
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(generated), len(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generated, total = build(args.output)
    print(f"Upserted {generated} curated docs records; {total} total records.")


if __name__ == "__main__":
    main()
