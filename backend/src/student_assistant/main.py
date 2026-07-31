"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from student_assistant.api.router import api_router
from student_assistant.repositories.mongo import close_client, ensure_indexes


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await ensure_indexes()
        yield
    finally:
        close_client()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Trợ lý Học viên - CP3 Backend",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_app()
