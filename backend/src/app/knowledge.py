"""Compatibility shim cho knowledge service cũ."""

from student_assistant.services.knowledge import best_similarity, search_kb


__all__ = ["best_similarity", "search_kb"]
