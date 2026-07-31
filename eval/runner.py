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
               "clarification object missing")
        if expected.get("clarification_field") and clar:
            _check("clarification_field",
                   clar.get("missing_field") == expected["clarification_field"],
                   f"expected={expected['clarification_field']}, "
                   f"got={clar.get('missing_field')}")

    # 7. Escalation
    if expected.get("escalation_required"):
        esc = actual.get("escalation")
        _check("escalation_required", esc is not None,
               "escalation object missing")
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
    # Load golden set
    with open(GOLDEN_SET, "r", encoding="utf-8") as f:
        golden = json.load(f)

    if cases_filter:
        golden = [c for c in golden if c["id"] in cases_filter]

    orchestrator = ChatbotOrchestrator()
    results: list[dict[str, Any]] = []
    passed_count = 0
    total = len(golden)

    print(f"\n{'='*60}")
    print(f"  EVAL RUNNER — {total} test cases")
    print(f"{'='*60}\n")

    for case in golden:
        case_id = case["id"]
        inp = case["input"]
        expected = case["expected"]

        # Convert input to orchestrator format
        msg = inp["message"]["content"]
        history = inp.get("conversation", {}).get("history", [])
        pending = inp.get("conversation", {}).get("pending_clarification")
        user_id = inp["metadata"]["user_id"]
        session_id = inp["metadata"]["session_id"]
        channel_id = inp["metadata"]["channel_id"]

        t0 = time.time()
        actual = orchestrator.process_message(
            message=msg,
            user_id=user_id,
            session_id=session_id,
            channel_id=channel_id,
            pending_clarification=pending,
            conversation_history=history,
        )
        elapsed_ms = round((time.time() - t0) * 1000)

        eval_result = evaluate_case(actual, expected)
        if eval_result["passed"]:
            passed_count += 1

        status = "✅ PASS" if eval_result["passed"] else "❌ FAIL"
        print(f"  {status}  {case_id}  ({elapsed_ms}ms)")

        if verbose or not eval_result["passed"]:
            for check in eval_result["checks"]:
                mark = "  ✓" if check["passed"] else "  ✗"
                print(f"    {mark} {check['name']}: {check['detail']}")
            if verbose:
                print(f"    → response: {actual.get('response', '')[:100]}...")
            print()

        results.append({
            "case_id": case_id,
            "description": case["description"],
            "passed": eval_result["passed"],
            "elapsed_ms": elapsed_ms,
            "actual_route": actual.get("route"),
            "actual_confidence": actual.get("confidence"),
            "actual_grounding": actual.get("grounding_status"),
            "actual_response_preview": actual.get("response", "")[:200],
            "checks": eval_result["checks"],
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
            "total": total,
            "passed": passed_count,
            "percentage": pct,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {out_file}")

    return passed_count, total


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Eval runner")
    parser.add_argument("--case", nargs="*", help="Run specific case IDs")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    run_eval(cases_filter=args.case, verbose=args.verbose)
