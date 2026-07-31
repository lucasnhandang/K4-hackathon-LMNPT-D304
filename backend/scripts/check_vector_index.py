"""Print Atlas Vector Search index readiness without exposing credentials."""

import asyncio

from student_assistant.core.config import settings
from student_assistant.repositories.mongo import close_client, get_db


async def main() -> None:
    try:
        indexes = await (
            get_db()
            .kb_documents.list_search_indexes(settings.vector_search_index)
            .to_list(length=1)
        )
        if not indexes:
            print(f"Index '{settings.vector_search_index}' was not found.")
            raise SystemExit(1)
        index = indexes[0]
        status = index.get("status", "UNKNOWN")
        queryable = bool(index.get("queryable", False))
        print(
            f"Index '{settings.vector_search_index}': "
            f"status={status}, queryable={queryable}"
        )
        if not queryable:
            raise SystemExit(2)
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
