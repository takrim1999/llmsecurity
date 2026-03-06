from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class RagDocument(BaseModel):
    """
    Representation of a retrieved document fed into the LLM context.
    """

    id: str
    content: str
    source: Optional[str] = None
    score: Optional[float] = None


class ChatCompletionRequest(BaseModel):
    """
    Simplified OpenAI-style chat completion request used by the gateway.
    """

    model: Optional[str] = None
    messages: list[ChatMessage]
    temperature: float = 0.0
    max_tokens: Optional[int] = Field(default=None, ge=1)
    rag_documents: list[RagDocument] = Field(
        default_factory=list,
        description="Optional retrieved documents treated as low-priority RAG context.",
    )


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage

