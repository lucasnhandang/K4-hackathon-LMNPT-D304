"""Create or update the MongoDB Atlas Vector Search index."""

import asyncio

from pymongo.operations import SearchIndexModel

from student_assistant.core.config import settings
from student_assistant.repositories.mongo import close_client, get_db


async def main() -> None:
    definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.embedding_dimensions,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "is_active"},
            {"type": "filter", "path": "source"},
        ]
    }
    model = SearchIndexModel(
        definition=definition,
        name=settings.vector_search_index,
        type="vectorSearch",
    )
    try:
        collection = get_db().kb_documents
        existing = await collection.list_search_indexes().to_list(length=None)
        names = {index.get("name") for index in existing}
        if settings.vector_search_index in names:
            await collection.update_search_index(
                settings.vector_search_index,
                definition,
            )
            operation = "update"
        else:
            await collection.create_search_index(model=model)
            operation = "create"
        print(
            f"Submitted {operation} for index "
            f"'{settings.vector_search_index}'. Wait for READY status in Atlas."
        )
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
