"""Compatibility shim. Dùng ``student_assistant.main`` cho code mới."""

from student_assistant.main import app, create_app


__all__ = ["app", "create_app"]
