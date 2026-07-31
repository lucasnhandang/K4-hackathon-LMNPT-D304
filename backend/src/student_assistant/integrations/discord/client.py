"""HTTP client gọi backend từ Discord process."""

import httpx


class BackendChatClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        normalized_base_url = base_url.rstrip("/")
        self.chat_url = f"{normalized_base_url}/chat"
        self.knowledge_url = f"{normalized_base_url}/knowledge/discord"
        self.timeout = httpx.Timeout(timeout_seconds)
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send_message(self, payload: dict) -> dict:
        if self._client is None:
            raise RuntimeError("Backend HTTP client chưa được khởi tạo")

        response = await self._client.post(self.chat_url, json=payload)
        response.raise_for_status()
        return response.json()

    async def ingest_knowledge(self, payload: dict) -> dict:
        if self._client is None:
            raise RuntimeError("Backend HTTP client chưa được khởi tạo")

        response = await self._client.post(self.knowledge_url, json=payload)
        response.raise_for_status()
        return response.json()
