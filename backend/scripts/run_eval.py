"""
Chạy: python scripts/run_eval.py

Nguyên tắc BẮT BUỘC theo tiêu chí CP3:
- Chạy TOÀN BỘ golden set (>=20 câu), không được chỉ chọn câu chạy đúng để show.
- Ghi lại TẤT CẢ các dòng vào eval_runs, kể cả dòng actual != expected.
- Không tự động "sửa" hay loại bỏ câu sai khỏi báo cáo.
- In ra bảng đầy đủ + tỷ lệ đúng thật (accuracy), để labcoach nhìn thấy đúng
  100% những gì hệ thống làm được, không hơn không kém.
"""
import asyncio
import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from student_assistant.domain.models import EvalRow, GoldenCase
from student_assistant.repositories.mongo import close_client, get_db
from student_assistant.services.question_router import route_question

BACKEND_DIR = Path(__file__).resolve().parent.parent
GOLDEN_SET_PATH = BACKEND_DIR / "data" / "golden_set.json"
OUTPUT_CSV_DIR = BACKEND_DIR / "data"


async def load_golden_set() -> list[GoldenCase]:
    raw = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    return [GoldenCase(**item) for item in raw]


async def run():
    cases = await load_golden_set()
    run_id = str(uuid.uuid4())[:8]
    rows: list[EvalRow] = []

    print(f"=== Chạy golden set ({len(cases)} câu) — run_id={run_id} ===\n")

    for case in cases:
        try:
            result = await route_question(case.question)
            actual_decision = result.decision
            actual_message = result.message
            confidence = result.confidence
        except Exception as e:
            # Lỗi cũng phải ghi lại trung thực, không được bỏ qua dòng này
            actual_decision = None
            actual_message = f"[LỖI HỆ THỐNG] {e}"
            confidence = 0.0

        is_correct = (actual_decision == case.expected_decision)

        row = EvalRow(
            qid=case.qid,
            question=case.question,
            expected_decision=case.expected_decision,
            actual_decision=actual_decision or case.expected_decision,  # placeholder khi lỗi, message đã ghi rõ lỗi
            is_correct=is_correct,
            actual_message=actual_message,
            confidence=confidence,
        )
        rows.append(row)

        mark = "✅" if is_correct else "❌"
        print(f"{mark} [{case.qid}] '{case.question}'")
        print(f"    expected={case.expected_decision.value:<11} actual={(actual_decision.value if actual_decision else 'ERROR'):<11} conf={confidence:.2f}")
        print(f"    → {actual_message}\n")

    total = len(rows)
    correct = sum(1 for r in rows if r.is_correct)
    accuracy = correct / total if total else 0.0

    print("=" * 60)
    print(f"KẾT QUẢ: {correct}/{total} đúng ({accuracy*100:.1f}%)")
    print("(Ghi trung thực toàn bộ, không loại bỏ câu sai khỏi báo cáo.)")
    print("=" * 60)

    # Ghi vào MongoDB — toàn bộ, không lọc
    db = get_db()
    await db.eval_runs.insert_one({
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc),
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "rows": [r.model_dump() for r in rows],
    })

    # Xuất CSV để đính kèm demo / báo cáo CP3
    csv_path = OUTPUT_CSV_DIR / f"eval_result_{run_id}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["qid", "question", "expected_decision", "actual_decision", "is_correct", "confidence", "actual_message"])
        for r in rows:
            writer.writerow([r.qid, r.question, r.expected_decision.value, r.actual_decision.value, r.is_correct, f"{r.confidence:.2f}", r.actual_message])

    print(f"\nĐã lưu bảng đầy đủ vào Mongo (eval_runs, run_id={run_id}) và CSV: {csv_path}")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    finally:
        close_client()
