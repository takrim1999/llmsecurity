from __future__ import annotations

from typing import Any

import httpx
from groq import AsyncGroq

from ..schemas.openai_compat import ChatCompletionRequest, ChatCompletionResponse
from ..settings import get_settings


class GroqClient:
    """
    Thin async wrapper around the official Groq client.

    This abstraction keeps the rest of the codebase decoupled from the SDK.
    """

    def __init__(self, client: AsyncGroq) -> None:
        self._client = client

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        settings = get_settings()

        try:
            response = await self._client.chat.completions.create(
                model=request.model or settings.groq_model,
                messages=[msg.model_dump(exclude_none=True) for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
            )
        except httpx.HTTPError as exc:
            # In later phases, normalize errors and surface them with structured reasons.
            raise RuntimeError("Groq API request failed") from exc

        return ChatCompletionResponse.model_validate(response.model_dump())


def get_groq_client() -> GroqClient:
    settings = get_settings()
    client = AsyncGroq(api_key=settings.groq_api_key)
    return GroqClient(client=client)

