"""Seed sample KB documents and generate Gemini embeddings.

Run from ``backend`` after installing the package:
    python scripts/seed_kb.py
"""

import asyncio
import hashlib
from datetime import datetime, timezone

from student_assistant.core.config import settings
from student_assistant.repositories.mongo import close_client, get_db
from student_assistant.services.embeddings import embed_documents


KB_DOCS = [
    {
        "title": "Deadline nộp bài weekly",
        "tags": ["deadline", "weekly", "nop-bai"],
        "content": (
            "Deadline nộp weekly là 12h00 trưa trước các buổi mentor duty. "
            "Các buổi mentor duty cố định diễn ra vào tối thứ 4 và thứ 7."
        ),
    },
    {
        "title": "Deadline nộp Capstone project",
        "tags": ["deadline", "capstone", "nop-bai"],
        "content": (
            "Deadline nộp Capstone project là 23h59 ngày Chủ Nhật cuối cùng "
            "của khóa. Nộp trễ dưới 24 tiếng bị trừ 10% điểm, trễ hơn 24 "
            "tiếng không được chấm."
        ),
    },
    {
        "title": "Lịch mentor duty",
        "tags": ["mentor", "lich", "duty"],
        "content": (
            "Mentor duty diễn ra tối thứ 4 (20h-22h) và tối thứ 7 "
            "(14h-16h) hàng tuần qua kênh Discord #mentor-duty."
        ),
    },
    {
        "title": "Cách nộp bài tập weekly",
        "tags": ["nop-bai", "huong-dan", "weekly"],
        "content": (
            "Nộp bài weekly qua form Google Form dán trong kênh #submission, "
            "đính kèm link GitHub repo và ảnh chụp kết quả chạy."
        ),
    },
    {
        "title": "Tiêu chí chấm điểm weekly",
        "tags": ["cham-diem", "tieu-chi", "weekly"],
        "content": (
            "Bài weekly chấm theo 3 tiêu chí: đúng yêu cầu (40%), code sạch "
            "(30%), có test case (30%). Không chấm nếu thiếu file README."
        ),
    },
    {
        "title": "Điều kiện nhận chứng chỉ hoàn thành khóa",
        "tags": ["chung-chi", "hoan-thanh", "dieu-kien"],
        "content": (
            "Học viên cần hoàn thành tối thiểu 80% số bài weekly và nộp đúng "
            "hạn Capstone project để đủ điều kiện nhận chứng chỉ."
        ),
    },
    {
        "title": "Chính sách nghỉ phép và bảo lưu",
        "tags": ["nghi-phep", "bao-luu", "chinh-sach"],
        "content": (
            "Học viên có thể xin bảo lưu tối đa 1 lần trong khóa bằng cách "
            "điền form bảo lưu và được Mod duyệt trong 3 ngày làm việc."
        ),
    },
    {
        "title": "Kênh hỗ trợ kỹ thuật",
        "tags": ["ho-tro", "ky-thuat", "discord"],
        "content": (
            "Lỗi cài đặt môi trường hoặc lỗi code cụ thể nên hỏi tại kênh "
            "#tech-support, kèm ảnh chụp lỗi và đoạn code liên quan."
        ),
    },
    {
        "title": "Cấu trúc chương trình học",
        "tags": ["chuong-trinh", "cau-truc", "lo-trinh"],
        "content": (
            "Khóa học gồm 6 module: Nhập môn, Backend cơ bản, Database, API "
            "nâng cao, Triển khai và Capstone project. Mỗi module kéo dài 2 tuần."
        ),
    },
    {
        "title": "Quy định điểm danh buổi live",
        "tags": ["diem-danh", "live", "quy-dinh"],
        "content": (
            "Điểm danh buổi live qua bot Discord bằng lệnh !checkin trong 10 "
            "phút đầu buổi học. Vắng quá 3 buổi không phép sẽ được Mod nhắc nhở."
        ),
    },
]


def _content_hash(title: str, content: str) -> str:
    value = f"{title}\n{content}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


async def main() -> None:
    try:
        texts = [
            f"Tiêu đề: {document['title']}\nNội dung: {document['content']}"
            for document in KB_DOCS
        ]
        vectors = await embed_documents(texts)
        db = get_db()
        now = datetime.now(timezone.utc)

        for document, vector in zip(KB_DOCS, vectors, strict=True):
            content_hash = _content_hash(
                document["title"],
                document["content"],
            )
            payload = {
                **document,
                "source": "sample_seed",
                "version": 1,
                "is_active": True,
                "embedding": vector,
                "embedding_model": settings.gemini_embedding_model,
                "embedding_dimensions": settings.embedding_dimensions,
                "content_hash": content_hash,
                "updated_at": now,
            }
            await db.kb_documents.update_one(
                {
                    "content_hash": content_hash,
                    "embedding_model": settings.gemini_embedding_model,
                },
                {
                    "$set": payload,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )

        print(
            f"Upserted {len(KB_DOCS)} KB documents with "
            f"{settings.gemini_embedding_model} "
            f"({settings.embedding_dimensions} dimensions)."
        )
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
