"""Run one read-only Gemini embedding + Atlas retrieval smoke test."""

import asyncio
import sys

from student_assistant.repositories.mongo import close_client
from student_assistant.services.grounding import retrieve_grounding


DEFAULT_QUERY = "Deadline nộp bài weekly là khi nào?"


async def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY
    try:
        result = await retrieve_grounding(query)
        print(
            f"method={result.method}, top_score={result.score:.4f}, "
            f"documents={len(result.documents)}"
        )
        for index, document in enumerate(result.documents, start=1):
            print(
                f"{index}. score={document['score']:.4f} "
                f"title={document.get('title', '')}"
            )
        if not result.documents:
            raise SystemExit(1)
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
