"""Evaluate chatbot against the 20 handbook test cases.

Reads test_cases_handbook_20.md, runs each input through ChatbotOrchestrator,
compares actual vs expected outputs, and writes a results table to eval/results_handbook_20.md.

Usage:
    cd codebase/backend
    python ../eval/run_handbook_20_tests.py [--data-path PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Fix Windows encoding for emoji output
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / "codebase" / "backend" / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# Add codebase/backend to path so chatbot_tools can be imported
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "codebase" / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from chatbot_tools.orchestrator import ChatbotOrchestrator
from chatbot_tools.registry import build_default_registry


# ---------------------------------------------------------------------------
# Parse the markdown test-case file
# ---------------------------------------------------------------------------

def parse_test_cases(md_path: Path) -> list[dict]:
    """Extract Case N, expected route/intent, and input JSON from the handbook md.

    Returns a list of dicts:
      {case_no, expected_route, expected_intent, label, input_json}
    """
    text = md_path.read_text(encoding="utf-8")

    # Split into case blocks
    case_pattern = re.compile(r"## Case (\d+)\s*[—–-]\s*(.+?)(?=\n###)", re.DOTALL)
    json_block = re.compile(r"```json\s*(\{.+?\})\s*```", re.DOTALL)

    cases: list[dict] = []
    for match in case_pattern.finditer(text):
        case_no = int(match.group(1))
        label = match.group(2).strip()
        rest = text[match.end():]

        # The first JSON block in the rest is the Input; second is the Output
        jsons = json_block.findall(rest)
        if len(jsons) < 2:
            print(f"  ⚠️  Case {case_no}: không tìm đủ JSON block, bỏ qua")
            continue

        input_json = json.loads(jsons[0])

        # Extract expected route/intent from the output JSON
        output_json = json.loads(jsons[1])
        expected_route = output_json.get("route", "")
        expected_intent = output_json.get("intent", "")

        # Parse the label for route and short description
        # e.g. "Case 1 — ANSWER · Quy định chuyên cần (lớp ④ đặc thù domain)"
        route_match = re.search(r"(ANSWER|CLARIFY|ESCALATE)", label)

        cases.append({
            "case_no": case_no,
            "expected_route": expected_route,
            "expected_intent": expected_intent,
            "label": label.strip(),
            "input_json": input_json,
        })

    cases.sort(key=lambda c: c["case_no"])
    return cases


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

def run_single_test(orchestrator: ChatbotOrchestrator, case: dict) -> dict:
    """Run one test case and return a result dict."""
    inp = case["input_json"]
    msg_obj = inp.get("message", {})
    content = msg_obj.get("content", "")
    meta = inp.get("metadata", {})
    conversation = inp.get("conversation", {})

    history = conversation.get("history", [])
    pending = conversation.get("pending_clarification", None)

    actual = orchestrator.process_message(
        message=content,
        user_id=meta.get("user_id", "test_user"),
        session_id=meta.get("session_id", "test_session"),
        channel_id=meta.get("channel_id", "test_channel"),
        pending_clarification=pending,
        conversation_history=history or None,
    )

    # --- Scoring ---
    exp_route = case["expected_route"]
    exp_intent = case["expected_intent"]
    act_route = actual.get("route", "")
    act_intent = actual.get("intent", "")

    route_match = act_route == exp_route
    intent_match = act_intent == exp_intent

    # For escalation intents, also accept if route is ESCALATE (flexible intent)
    if exp_route == "ESCALATE":
        intent_match = intent_match or (act_route == "ESCALATE")

    # For CLARIFY, also accept if route is CLARIFY (intent can differ)
    if exp_route == "CLARIFY":
        intent_match = intent_match or (act_route == "CLARIFY")

    overall_pass = route_match and intent_match

    # Check if response is empty or too short (possible hallucination / failure)
    response_text = actual.get("response", "")
    has_response = len(response_text.strip()) > 5

    return {
        "case_no": case["case_no"],
        "label": case["label"],
        "expected_route": exp_route,
        "actual_route": act_route,
        "route_ok": route_match,
        "expected_intent": exp_intent,
        "actual_intent": act_intent,
        "intent_ok": intent_match,
        "overall_pass": overall_pass,
        "confidence": actual.get("confidence", 0),
        "grounding": actual.get("grounding_status", "unknown"),
        "has_response": has_response,
        "response_preview": response_text[:150].replace("\n", " "),
        "actual_full": actual,
    }


# ---------------------------------------------------------------------------
# Generate markdown results
# ---------------------------------------------------------------------------

def write_results_md(results: list[dict], out_path: Path) -> None:
    """Write a comprehensive markdown report."""
    total = len(results)
    passed = sum(1 for r in results if r["overall_pass"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0

    # Per-route stats
    route_stats: dict[str, dict] = {}
    for r in results:
        er = r["expected_route"]
        if er not in route_stats:
            route_stats[er] = {"total": 0, "pass": 0}
        route_stats[er]["total"] += 1
        if r["overall_pass"]:
            route_stats[er]["pass"] += 1

    # Per-class stats (layer)
    class_map = {
        1: ("① nguồn sự thật", [10, 11, 12, 18]),
        2: ("② mơ hồ/thiếu thông tin", [3, 7, 19]),
        3: ("③ ngoài phạm vi/thẩm quyền", [4, 5, 13, 14]),
        4: ("④ đặc thù domain", [1, 15, 16]),
    }
    # Build a lookup for each case
    result_map = {r["case_no"]: r for r in results}

    lines: list[str] = []
    lines.append(f"# Kết quả eval — Handbook 20 Test Cases")
    lines.append(f"")
    lines.append(f"**Ngày chạy:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")
    lines.append(f"## Tổng quan")
    lines.append(f"")
    lines.append(f"| Chỉ số | Giá trị |")
    lines.append(f"|---|---|")
    lines.append(f"| Tổng số case | {total} |")
    lines.append(f"| ✅ Pass | {passed} |")
    lines.append(f"| ❌ Fail | {failed} |")
    lines.append(f"| Tỷ lệ pass | **{pass_rate:.1f}%** |")
    lines.append(f"")

    # Route breakdown
    lines.append(f"### Phân tích theo Route")
    lines.append(f"")
    lines.append(f"| Route | Tổng | Pass | Tỷ lệ |")
    lines.append(f"|---|---|---|---|")
    for route in ["ANSWER", "CLARIFY", "ESCALATE"]:
        s = route_stats.get(route, {"total": 0, "pass": 0})
        rate = (s["pass"] / s["total"] * 100) if s["total"] else 0
        lines.append(f"| {route} | {s['total']} | {s['pass']} | {rate:.0f}% |")
    lines.append(f"")

    # Class breakdown
    lines.append(f"### Phân tích theo Lớp chỗ khó")
    lines.append(f"")
    lines.append(f"| Lớp | Case | Tổng | Pass | Tỷ lệ |")
    lines.append(f"|---|---|---|---|---|")
    for cls_id, (cls_name, case_nos) in class_map.items():
        total_cls = 0
        pass_cls = 0
        for cn in case_nos:
            if cn in result_map:
                total_cls += 1
                if result_map[cn]["overall_pass"]:
                    pass_cls += 1
        rate = (pass_cls / total_cls * 100) if total_cls else 0
        case_str = ", ".join(str(cn) for cn in case_nos)
        lines.append(f"| {cls_name} | {case_str} | {total_cls} | {pass_cls} | {rate:.0f}% |")
    lines.append(f"")

    # Detailed table
    lines.append(f"## Chi tiết từng Case")
    lines.append(f"")
    lines.append(f"| Case | Route | Intent | Pass | Confidence | Grounding | Response preview |")
    lines.append(f"|---|---|---|---|---|---|---|")
    for r in results:
        status = "✅" if r["overall_pass"] else "❌"
        route_icon = "🟢" if r["route_ok"] else "🔴"
        intent_icon = "🟢" if r["intent_ok"] else "🔴"
        preview = r["response_preview"][:80].replace("|", "\\|")
        lines.append(
            f"| {r['case_no']} | {route_icon} {r['expected_route']}→{r['actual_route']} "
            f"| {intent_icon} {r['expected_intent'][:30]} "
            f"| {status} | {r['confidence']:.2f} | {r['grounding']} | {preview} |"
        )
    lines.append(f"")

    # Failed cases detail
    failed_cases = [r for r in results if not r["overall_pass"]]
    if failed_cases:
        lines.append(f"## Chi tiết các Case FAIL")
        lines.append(f"")
        for r in failed_cases:
            lines.append(f"### Case {r['case_no']}: {r['label'][:80]}")
            lines.append(f"")
            lines.append(f"- **Expected route:** `{r['expected_route']}` → **Actual:** `{r['actual_route']}` {'✅' if r['route_ok'] else '❌'}")
            lines.append(f"- **Expected intent:** `{r['expected_intent']}` → **Actual:** `{r['actual_intent']}` {'✅' if r['intent_ok'] else '❌'}")
            lines.append(f"- **Confidence:** {r['confidence']:.2f}")
            lines.append(f"- **Grounding:** {r['grounding']}")
            lines.append(f"- **Response preview:** {r['response_preview'][:200]}")
            lines.append(f"")
            # Show full response
            full_resp = r["actual_full"].get("response", "")
            lines.append(f"<details><summary>Full response</summary>")
            lines.append(f"")
            lines.append(f"```")
            lines.append(full_resp[:500])
            lines.append(f"```")
            lines.append(f"</details>")
            lines.append(f"")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Eval chatbot against handbook 20 test cases")
    parser.add_argument(
        "--test-file",
        default=str(Path(__file__).resolve().parent / "test_cases_handbook_20.md"),
        help="Path to test_cases_handbook_20.md",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "results_handbook_20.md"),
        help="Output path for results markdown",
    )
    parser.add_argument("--data-path", help="Path to official_sources.json")
    args = parser.parse_args()

    test_file = Path(args.test_file)
    output_file = Path(args.output)

    print("=" * 60)
    print("🧪  Eval: Handbook 20 Test Cases")
    print("=" * 60)
    print(f"  Test file : {test_file}")
    print(f"  Output    : {output_file}")
    print()

    # Parse test cases
    cases = parse_test_cases(test_file)
    print(f"  📄 Đã parse {len(cases)} test cases")
    if not cases:
        print("  ❌ Không tìm thấy test case nào!")
        sys.exit(1)
    print()

    # Build orchestrator
    print("  🔧 Đang khởi tạo ChatbotOrchestrator ...")
    try:
        data_path = args.data_path or None
        registry = build_default_registry(data_path)
        orchestrator = ChatbotOrchestrator(registry)
        print("  ✅ Orchestrator ready")
    except Exception as e:
        print(f"  ❌ Lỗi khởi tạo orchestrator: {e}")
        sys.exit(1)
    print()

    # Run tests
    print("  🚀 Đang chạy test ...")
    print("-" * 60)
    results: list[dict] = []
    for case in cases:
        result = run_single_test(orchestrator, case)
        results.append(result)
        status = "✅" if result["overall_pass"] else "❌"
        print(
            f"  {status} Case {result['case_no']:2d} | "
            f"{result['expected_route']:>8s}→{result['actual_route']:<8s} | "
            f"{result['expected_intent'][:35]}"
        )
    print("-" * 60)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["overall_pass"])
    failed = total - passed
    print(f"\n  📊 Kết quả: {passed}/{total} pass ({passed/total*100:.1f}%)")
    print(f"     ✅ Pass: {passed}")
    print(f"     ❌ Fail: {failed}")

    # Write results
    write_results_md(results, output_file)
    print(f"\n  📝 Kết quả đã lưu: {output_file}")
    print()


if __name__ == "__main__":
    main()
