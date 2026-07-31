"""Compatibility shim cho MongoDB module cũ."""

from student_assistant.repositories.mongo import (
    close_client,
    ensure_indexes,
    get_client,
    get_db,
)


__all__ = ["close_client", "ensure_indexes", "get_client", "get_db"]
