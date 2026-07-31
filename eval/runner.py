"""Eval runner — chạy golden set qua ChatbotOrchestrator và so sánh kết quả.

Usage:
    python -m eval.runner                          # chạy tất cả cases
    python -m eval.runner --case case_01 case_03   # chạy 1 vài cases
    python -m eval.runner --verbose                # in chi tiết từng case
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

# ── paths ──────────────────────────────────────────────────────────────
EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"

# ── import chatbot ─────────────────────────────────────────────────────
sys.path.insert(0, str(EVAL_DIR.parent / "codebase" / "backend"))
from chatbot_tools.orchestrator import ChatbotOrchestrator


# ═══════════════════════════════════════════════════════════════════════
# Markdown report
# ═══════════════════════════════════════════════════════════════════════

def _escape_markdown_cell(value: Any) -> str:
    """Escape a value so it can be rendered safely inside a Markdown table."""
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def write_markdown_report(
    out_file: Path,
    timestamp: str,
    execution_mode: str,
    results: list[dict[str, Any]],
    passed_count: int,
    total: int,
    percentage: float,
    categories: dict[str, list[dict[str, Any]]],
    category_labels: dict[str, str],
) -> None:
    """Write a human-readable evaluation table next to the raw JSON result."""
    failed_count = total - passed_count
    route_stats: dict[str, dict[str, int]] = {}

    for result in results:
        route = result.get("expected_route") or "(missing)"
        stats = route_stats.setdefault(route, {"total": 0, "passed": 0})
        stats["total"] += 1
        if result["passed"]:
            stats["passed"] += 1

    lines = [
        "# Kết quả evaluation — Golden set",
        "",
        f"**Run ID:** `{timestamp}`  ",
        f"**Golden set:** `eval/golden_set.json`  ",
        f"**Chế độ chạy:** `{execution_mode}`",
        "",
        "## Tổng quan",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---:|",
        f"| Tổng số case | {total} |",
        f"| Pass | {passed_count} |",
        f"| Fail | {failed_count} |",
        f"| Tỷ lệ pass | **{percentage:.1f}%** |",
        "",
        "## Kết quả theo expected route",
        "",
        "| Route | Tổng | Pass | Tỷ lệ |",
        "|---|---:|---:|---:|",
    ]

    for route in ("ANSWER", "CLARIFY", "ESCALATE", "(missing)"):
        stats = route_stats.get(route)
        if not stats:
            continue
        rate = stats["passed"] / stats["total"] * 100 if stats["total"] else 0
        lines.append(
            f"| {_escape_markdown_cell(route)} | {stats['total']} | "
            f"{stats['passed']} | {rate:.1f}% |"
        )

    lines.extend([
        "",
        "## Kết quả theo nhóm",
        "",
        "| Nhóm | Tổng | Pass | Tỷ lệ |",
        "|---|---:|---:|---:|",
    ])
    for category, category_results in categories.items():
        if not category_results:
            continue
        category_passed = sum(1 for result in category_results if result["passed"])
        category_total = len(category_results)
        category_rate = category_passed / category_total * 100
        lines.append(
            f"| {_escape_markdown_cell(category_labels[category])} | "
            f"{category_total} | {category_passed} | {category_rate:.1f}% |"
        )

    lines.extend([
        "",
        "## Chi tiết từng case",
        "",
        "| Case | Mô tả | Kết quả | Route expected → actual | Intent expected → actual | Confidence | Grounding | Thời gian | Response preview |",
        "|---|---|:---:|---|---|---:|---|---:|---|",
    ])
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(
            f"| `{_escape_markdown_cell(result['case_id'])}` "
            f"| {_escape_markdown_cell(result['description'])} "
            f"| {status} "
            f"| {_escape_markdown_cell(result['expected_route'])} → "
            f"{_escape_markdown_cell(result['actual_route'])} "
            f"| {_escape_markdown_cell(result['expected_intent'])} → "
            f"{_escape_markdown_cell(result['actual_intent'])} "
            f"| {_escape_markdown_cell(result['actual_confidence'])} "
            f"| {_escape_markdown_cell(result['actual_grounding'])} "
            f"| {result['elapsed_ms']} ms "
            f"| {_escape_markdown_cell(result['actual_response_preview'])} |"
        )

    failed_results = [result for result in results if not result["passed"]]
    if failed_results:
        lines.extend(["", "## Chi tiết các case fail", ""])
        for result in failed_results:
            lines.extend([
                f"### `{result['case_id']}` — {_escape_markdown_cell(result['description'])}",
                "",
            ])
            for turn in result["turns"]:
                if len(result["turns"]) > 1:
                    lines.extend([f"**Turn {turn['turn']}**", ""])
                for check in turn["checks"]:
                    mark = "PASS" if check["passed"] else "FAIL"
                    lines.append(
                        f"- {mark} — `{check['name']}`: {check['detail']}"
                    )
                lines.extend([
                    "",
                    f"> {_escape_markdown_cell(turn['actual_response_preview'])}",
                    "",
                ])

    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# 评判逻辑
# ═══════════════════════════════════════════════════════════════════════

def evaluate_case(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """So sánh output thực tế vs kỳ vọng, trả về dict chi tiết."""
    checks: list[dict[str, Any]] = []

    def _check(name: str, passed: bool, detail: str = ""):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # 1. Route
    exp_route = expected.get("route")
    act_route = actual.get("route", "")
    _check("route", act_route == exp_route,
           f"expected={exp_route}, got={act_route}")

    # 2. Confidence
    act_conf = actual.get("confidence", 0)
    if "confidence_min" in expected:
        _check("confidence_min", act_conf >= expected["confidence_min"],
               f"expected>={expected['confidence_min']}, got={act_conf}")
    if "confidence_max" in expected:
        _check("confidence_max", act_conf <= expected["confidence_max"],
               f"expected<={expected['confidence_max']}, got={act_conf}")

    # 3. Grounding status
    exp_gs = expected.get("grounding_status")
    act_gs = actual.get("grounding_status", "")
    if exp_gs:
        _check("grounding_status", act_gs == exp_gs,
               f"expected={exp_gs}, got={act_gs}")

    # 4. Response keywords (ít nhất 1 từ khóa xuất hiện)
    resp = actual.get("response", "")
    keywords = expected.get("response_keywords", [])
    if keywords:
        found = [kw for kw in keywords if kw.lower() in resp.lower()]
        _check("response_keywords", len(found) > 0,
               f"matched={found}, expected_any_of={keywords}")

    # 5. Citations
    if expected.get("citations_required"):
        citations = actual.get("citations", [])
        _check("citations_required", len(citations) > 0,
               f"got {len(citations)} citations")

    # 6. Clarification
    if expected.get("clarification_required"):
        clar = actual.get("clarification")
        _check("clarification_required", clar is not None,
               "clarification object present" if clar is not None
               else "clarification object missing")
        if expected.get("clarification_field") and clar:
            _check("clarification_field",
                   clar.get("missing_field") == expected["clarification_field"],
                   f"expected={expected['clarification_field']}, "
                   f"got={clar.get('missing_field')}")

    # 7. Escalation
    if expected.get("escalation_required"):
        esc = actual.get("escalation")
        _check("escalation_required", esc is not None,
               "escalation object present" if esc is not None
               else "escalation object missing")
        if expected.get("escalation_target") and esc:
            _check("escalation_target",
                   esc.get("target") == expected["escalation_target"],
                   f"expected={expected['escalation_target']}, "
                   f"got={esc.get('target')}")

    passed = all(c["passed"] for c in checks)
    return {"passed": passed, "checks": checks}


# ═══════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════

def run_eval(cases_filter: list[str] | None = None, verbose: bool = False):
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Load golden set
    with open(GOLDEN_SET, "r", encoding="utf-8") as f:
        golden = json.load(f)

    if cases_filter:
        golden = [c for c in golden if c["id"] in cases_filter]

    orchestrator = ChatbotOrchestrator()
    execution_mode = "openrouter_rag" if orchestrator.rag is not None else "offline_local"
    results: list[dict[str, Any]] = []
    passed_count = 0
    total = len(golden)

    print(f"\n{'='*60}")
    print(f"  EVAL RUNNER — {total} test cases")
    print(f"{'='*60}\n")

    for case in golden:
        case_id = case["id"]
        t0 = time.time()
        turn_specs = case.get("turns")
        if turn_specs is None:
            turn_specs = [{"input": case["input"], "expected": case["expected"]}]

        turn_results: list[dict[str, Any]] = []
        previous_actual: dict[str, Any] | None = None

        for turn_index, turn in enumerate(turn_specs, start=1):
            inp = turn["input"]
            expected = turn["expected"]

            # Convert input to orchestrator format. In a multiturn case, pass the
            # clarification actually returned by the preceding turn so the test
            # validates a real state transition instead of a hard-coded shortcut.
            msg = inp["message"]["content"]
            history = inp.get("conversation", {}).get("history", [])
            pending = inp.get("conversation", {}).get("pending_clarification")
            if previous_actual is not None and pending is not None:
                pending = previous_actual.get("clarification")

            actual = orchestrator.process_message(
                message=msg,
                user_id=inp["metadata"]["user_id"],
                session_id=inp["metadata"]["session_id"],
                channel_id=inp["metadata"]["channel_id"],
                pending_clarification=pending,
                conversation_history=history,
                cohort=(
                    inp.get("learning_context", {}).get("cohort")
                    or inp.get("runtime", {}).get("cohort")
                ),
                at=inp["metadata"].get("timestamp"),
            )
            turn_eval = evaluate_case(actual, expected)
            turn_results.append({
                "turn": turn_index,
                "passed": turn_eval["passed"],
                "expected_route": expected.get("route"),
                "actual_intent": actual.get("intent"),
                "expected_intent": expected.get("intent"),
                "actual_route": actual.get("route"),
                "actual_confidence": actual.get("confidence"),
                "actual_grounding": actual.get("grounding_status"),
                "actual_response_preview": actual.get("response", "")[:200],
                "checks": turn_eval["checks"],
            })
            previous_actual = actual

        elapsed_ms = round((time.time() - t0) * 1000)

        case_passed = all(turn["passed"] for turn in turn_results)
        if case_passed:
            passed_count += 1

        status = "✅ PASS" if case_passed else "❌ FAIL"
        print(f"  {status}  {case_id}  ({elapsed_ms}ms)")

        if verbose or not case_passed:
            for turn_result in turn_results:
                if len(turn_results) > 1:
                    print(f"    Turn {turn_result['turn']}: {turn_result['actual_route']}")
                for check in turn_result["checks"]:
                    mark = "      ✓" if check["passed"] else "      ✗"
                    print(f"{mark} {check['name']}: {check['detail']}")
                if verbose:
                    preview = turn_result["actual_response_preview"][:100]
                    print(f"      → response: {preview}...")
            print()

        final_turn = turn_results[-1]
        results.append({
            "case_id": case_id,
            "description": case["description"],
            "passed": case_passed,
            "elapsed_ms": elapsed_ms,
            "expected_route": final_turn["expected_route"],
            "actual_route": final_turn["actual_route"],
            "expected_intent": final_turn["expected_intent"],
            "actual_intent": final_turn["actual_intent"],
            "actual_confidence": final_turn["actual_confidence"],
            "actual_grounding": final_turn["actual_grounding"],
            "actual_response_preview": final_turn["actual_response_preview"],
            "checks": final_turn["checks"],
            "turns": turn_results,
        })

    # ── Summary ────────────────────────────────────────────────────────
    pct = round(passed_count / total * 100, 1) if total else 0
    print(f"\n{'='*60}")
    print(f"  RESULT: {passed_count}/{total} passed ({pct}%)")
    print(f"{'='*60}\n")

    # ── Category breakdown ─────────────────────────────────────────────
    categories = {
        "①_not_in_doc": [],    # cases 10, 11, 12, 18
        "②_ambiguous": [],     # cases 3, 7, 19
        "③_forbidden": [],     # cases 4, 5, 13, 14
        "④_consequence": [],   # cases 1, 15, 16
        "other": [],           # rest
    }
    cat_map = {
        "case_01": "④_consequence", "case_02": "other",
        "case_03": "②_ambiguous", "case_04": "③_forbidden",
        "case_05": "③_forbidden", "case_06": "other",
        "case_07": "②_ambiguous", "case_08": "other",
        "case_09": "other", "case_10": "①_not_in_doc",
        "case_11": "①_not_in_doc", "case_12": "①_not_in_doc",
        "case_13": "③_forbidden", "case_14": "③_forbidden",
        "case_15": "④_consequence", "case_16": "④_consequence",
        "case_17": "other", "case_18": "①_not_in_doc",
        "case_19": "②_ambiguous", "case_20": "other",
    }
    for r in results:
        cat = cat_map.get(r["case_id"], "other")
        categories[cat].append(r)

    cat_labels = {
        "①_not_in_doc": "① Không có trong tài liệu",
        "②_ambiguous": "② Mơ hồ/thiếu ngữ cảnh",
        "③_forbidden": "③ Đòi thứ không được phép",
        "④_consequence": "④ Sai gây hậu quả thật",
        "other": "Khác",
    }
    print("  Phân loại kết quả:")
    for cat_key, cat_results in categories.items():
        if cat_results:
            p = sum(1 for r in cat_results if r["passed"])
            t = len(cat_results)
            print(f"    {cat_labels[cat_key]}: {p}/{t}")

    # ── Save results ───────────────────────────────────────────────────
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_file = RESULTS_DIR / f"eval_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "execution_mode": execution_mode,
            "total": total,
            "passed": passed_count,
            "percentage": pct,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {out_file}")

    markdown_file = RESULTS_DIR / f"eval_{ts}.md"
    write_markdown_report(
        out_file=markdown_file,
        timestamp=ts,
        execution_mode=execution_mode,
        results=results,
        passed_count=passed_count,
        total=total,
        percentage=pct,
        categories=categories,
        category_labels=cat_labels,
    )
    print(f"  Markdown report saved to: {markdown_file}")

    return passed_count, total


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Eval runner")
    parser.add_argument("--case", nargs="*", help="Run specific case IDs")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    run_eval(cases_filter=args.case, verbose=args.verbose)
