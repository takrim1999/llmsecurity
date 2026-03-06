from fastapi import APIRouter, Depends

from ..connectors.groq_connector import GroqClient, get_groq_client
from ..schemas.openai_compat import ChatCompletionRequest, ChatCompletionResponse


router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    groq_client: GroqClient = Depends(get_groq_client),
) -> ChatCompletionResponse:
    """
    Minimal OpenAI-compatible chat completions endpoint backed by Groq.

    PCFI checks are applied in middleware before this handler is invoked.
    """

    completion = await groq_client.chat_completion(request)
    return completion


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

