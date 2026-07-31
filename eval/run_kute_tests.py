"""Run KUTE test cases through the chatbot and output results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / "codebase" / "backend" / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "codebase" / "backend"))

from chatbot_tools.orchestrator import ChatbotOrchestrator
from chatbot_tools.registry import build_default_registry

# 20 KUTE test cases
TEST_CASES = [
    {
        "id": "01",
        "kute_id": "KUTE-REG-007",
        "topic": "Weekly Report",
        "input": "lệnh báo cáo tuần",
        "expect": "Trả lời đúng chi tiết về lệnh nộp weekly report, không lặp mẫu chung",
    },
    {
        "id": "02",
        "kute_id": "KUTE-REG-096",
        "topic": "Weekly Report",
        "input": "hướng dẫn nộp báo cáo tuần",
        "expect": "Trả lời đúng hướng dẫn nộp weekly report, không lặp mẫu",
    },
    {
        "id": "03",
        "kute_id": "KUTE-REG-180",
        "topic": "XP / Mentor Duty",
        "input": "mentor duty có xp k",
        "expect": "Trả lời về XP của mentor duty, phân biệt với workshop/office hours",
    },
    {
        "id": "04",
        "kute_id": "KUTE-REG-201",
        "topic": "Daily Stand-up",
        "input": "daily có tác dụng và vai trò gì",
        "expect": "Trả lời về tác dụng/vai trò của daily, không chỉ nói giờ nộp",
    },
    {
        "id": "05",
        "kute_id": "KUTE-REG-158",
        "topic": "Team XP",
        "input": "Làm sao để xem tổng điểm kinh nghiệm hiện có của nhóm",
        "expect": "Trả lời cách xem tổng XP team, phân biệt XP cá nhân vs team",
    },
    {
        "id": "06",
        "kute_id": "KUTE-REG-109",
        "topic": "Gate + Weekly Report",
        "input": "gate khi nào? và nộp weekly submit khi nào? 2 sự kiện này khác gì nhau",
        "expect": "Trả lời đầy đủ 2 ý: deadline gate và deadline weekly, phân biệt 2 cái",
    },
    {
        "id": "07",
        "kute_id": "KUTE-REG-002",
        "topic": "Team / Đề tài",
        "input": "nhóm mình có 4 người nhưng có 2 bạn nghỉ học, giờ còn 2 người thì có join vào nhóm khác hoặc đổi đề tài khác được không",
        "expect": "Trả lời về quyền thay đổi nhóm/đề tài, hướng dẫn tạo ticket nếu cần",
    },
    {
        "id": "08",
        "kute_id": "KUTE-REG-189",
        "topic": "Lịch tối nay",
        "input": "tối nay",
        "expect": "Trả lời lịch sự kiện tối nay theo dữ liệu hiện hành, không dùng từ 'thường'",
    },
    {
        "id": "09",
        "kute_id": "KUTE-REG-198",
        "topic": "Lịch tối nay",
        "input": "tối nay có sự kiện gì ?",
        "expect": "Trả lời lịch sự kiện tối nay, phân biệt workshop/mentor duty",
    },
    {
        "id": "10",
        "kute_id": "KUTE-REG-216",
        "topic": "Lịch tối nay",
        "input": "tối nay có gì không nhỉ",
        "expect": "Trả lời lịch tối nay, không dùng suy đoán",
    },
    {
        "id": "11",
        "kute_id": "KUTE-REG-193",
        "topic": "Workshop vs Mentor Duty",
        "input": "tối thứ 5 là workshop hay là mentor duty vậy ? Hay từ tuần này 2 cái là 1 ?",
        "expect": "Phân biệt workshop và mentor duty, trả lời từng ý",
    },
    {
        "id": "12",
        "kute_id": "KUTE-REG-226",
        "topic": "Link slide hackathon",
        "input": "cho tôi link slide buổi hackathon hôm nay",
        "expect": "Trả lời link hoặc nói rõ không tìm thấy, không chỉ hướng kênh khác",
    },
    {
        "id": "13",
        "kute_id": "KUTE-REG-215",
        "topic": "Tài liệu workshop",
        "input": "Tìm cho tôi tài liệu workshop 2",
        "expect": "Trả lời trực tiếp kết quả tìm kiếm, không chuyển chủ đề",
    },
    {
        "id": "14",
        "kute_id": "KUTE-REG-174",
        "topic": "Tổng hợp tin nhắn nhóm",
        "input": "tổng hợp tin nhắn thông tin trong nhóm từ 18h đến 20h25 phút",
        "expect": "Trả lời hoặc nói rõ giới hạn, không chỉ chuyển Mod",
    },
    {
        "id": "15",
        "kute_id": "KUTE-REG-176",
        "topic": "Đổi tên team",
        "input": "nhóm mọi người đặt tên ở đâu nhỉ, t thấy mọi người có mấy cái tên vui vui mà nhón t được ghép tự động nên chưa tìm ra chỗ đổi",
        "expect": "Trả lời về cách đặt tên team, không bịa lệnh",
    },
    {
        "id": "16",
        "kute_id": "KUTE-NR-001",
        "topic": "Kiểm tra đề tài",
        "input": "cách kiểm tra 1 đề tài đã có nhóm nào chọn chưa",
        "expect": "Phải có phản hồi, không im lặng",
    },
    {
        "id": "17",
        "kute_id": "KUTE-NR-003",
        "topic": "Gate 1",
        "input": "Gate 1 nộp những gì và thời gian nộp là bao giờ",
        "expect": "Phải có phản hồi về gate 1 hoặc nói rõ không có dữ liệu",
    },
    {
        "id": "18",
        "kute_id": "KUTE-NR-004",
        "topic": "Codelabs cá nhân",
        "input": "Hi. về các bài codelabs trên lớp tôi làm một bài với nhóm nhưng tôi submit bài cá nhân được ko",
        "expect": "Phải có phản hồi về quy định nộp codelabs",
    },
    {
        "id": "19",
        "kute_id": "KUTE-NR-005",
        "topic": "Tìm bài Jira",
        "input": "tìm cho mình bài setup jira, mình bị trôi mất tin nhắn đó rồi.",
        "expect": "Phải có phản hồi, tìm hoặc hướng dẫn tìm",
    },
    {
        "id": "20",
        "kute_id": "KUTE-REG-031",
        "topic": "Nộp báo cáo mentor duty",
        "input": "nộp báo cáo buổi mentor duty ở đâu",
        "expect": "Trả lời đúng về mentor duty, không nhầm với daily/weekly",
    },
]


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    registry = build_default_registry()
    orch = ChatbotOrchestrator(registry)

    results = []

    print("=" * 80)
    print("🧪 KUTE TEST SUITE — 20 Test Cases")
    print("=" * 80)

    for tc in TEST_CASES:
        response = orch.process_message(
            message=tc["input"],
            user_id="kute_test",
            session_id=f"kute_session_{tc['id']}",
            channel_id="kute_channel",
        )

        resp_text = response.get("response", "")
        intent = response.get("intent", "unknown")
        route = response.get("route", "UNKNOWN")
        confidence = response.get("confidence", 0)
        grounding = response.get("grounding_status", "unknown")

        result = {
            "id": tc["id"],
            "kute_id": tc["kute_id"],
            "topic": tc["topic"],
            "input": tc["input"],
            "response": resp_text,
            "intent": intent,
            "route": route,
            "confidence": confidence,
            "grounding": grounding,
            "expect": tc["expect"],
        }
        results.append(result)

        print(f"\n{'─' * 80}")
        print(f"📝 Test {tc['id']} | {tc['kute_id']} | {tc['topic']}")
        print(f"❓ Input: {tc['input']}")
        print(f"🤖 Response: {resp_text[:200]}{'...' if len(resp_text) > 200 else ''}")
        print(f"📊 Intent: {intent} | Route: {route} | Confidence: {confidence:.2f} | Grounding: {grounding}")

    # Save results
    output_path = Path(__file__).parent / "kute_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 80}")
    print(f"✅ Results saved to {output_path}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
