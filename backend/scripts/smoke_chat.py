"""Run a read-only grounded Gemini response smoke test."""

import asyncio
import sys

from student_assistant.repositories.mongo import close_client
from student_assistant.services.gemini import generate_chat_response
from student_assistant.services.grounding import (
    build_grounding_context,
    retrieve_grounding,
)


DEFAULT_QUERY = "Deadline nộp bài weekly là khi nào?"


async def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY
    try:
        grounding = await retrieve_grounding(query)
        generated = await generate_chat_response(
            query,
            [],
            build_grounding_context(grounding),
        )
        print(
            f"grounding_score={grounding.score:.4f}, "
            f"action={generated.action}"
        )
        print(generated.reply)
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
