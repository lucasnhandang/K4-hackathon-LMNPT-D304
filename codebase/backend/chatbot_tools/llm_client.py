"""OpenRouter LLM client for the Discord student assistant.

Provides a lightweight HTTP client for calling OpenRouter's chat completions API.
Uses stdlib only (urllib + json) — no external dependencies.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "google/gemini-2.0-flash-001"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 1
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1024


@dataclass
class LLMConfig:
    """Configuration for the OpenRouter LLM client."""

    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    app_name: str = "AI20K-Student-Assistant"
    site_url: str = "http://localhost"
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Load configuration from environment variables."""
        return cls(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url=os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            model=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
            app_name=os.environ.get("OPENROUTER_APP_NAME", "AI20K-Student-Assistant"),
            site_url=os.environ.get("OPENROUTER_SITE_URL", "http://localhost"),
        )


@dataclass
class LLMResponse:
    """Response from the LLM."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# OpenRouter Client
# ---------------------------------------------------------------------------


class LLMClient:
    """Lightweight OpenRouter chat completions client.

    Uses urllib (stdlib) — no external dependencies required.
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        if not self.config.api_key:
            logger.warning(
                "OPENROUTER_API_KEY is not set. LLM calls will fail."
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to OpenRouter.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            model: Override model (default: config.model)
            temperature: Override temperature (default: config.temperature)
            max_tokens: Override max_tokens (default: config.max_tokens)

        Returns:
            LLMResponse with the assistant's reply.

        Raises:
            LLMError: On API errors, network issues, or invalid responses.
        """
        url = f"{self.config.base_url}/chat/completions"
        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.app_name,
        }

        body = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None

        for attempt in range(1 + self.config.max_retries):
            try:
                request = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                    response_body = response.read().decode("utf-8")

                data = json.loads(response_body)
                return self._parse_response(data)

            except urllib.error.HTTPError as error:
                error_body = error.read().decode("utf-8", errors="replace")
                last_error = LLMError(
                    f"HTTP {error.code}: {error_body[:500]}"
                )
                logger.warning(
                    "LLM API error (attempt %d/%d): %s",
                    attempt + 1,
                    1 + self.config.max_retries,
                    last_error,
                )

            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_error = LLMError(f"Network error: {error}")
                logger.warning(
                    "LLM network error (attempt %d/%d): %s",
                    attempt + 1,
                    1 + self.config.max_retries,
                    last_error,
                )

            except (json.JSONDecodeError, KeyError, ValueError) as error:
                last_error = LLMError(f"Invalid response: {error}")
                logger.warning("LLM parse error: %s", last_error)
                break  # Don't retry parse errors

        raise last_error or LLMError("LLM call failed after all retries")

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        """Parse the OpenRouter API response."""
        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason", "")
        except (KeyError, IndexError) as error:
            raise LLMError(f"Unexpected response structure: {error}") from error

        usage = data.get("usage", {})
        model = data.get("model", self.config.model)

        return LLMResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            finish_reason=finish_reason,
            raw=data,
        )

    def is_available(self) -> bool:
        """Check if the client is configured and ready to use."""
        return bool(self.config.api_key)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Raised when an LLM API call fails."""
