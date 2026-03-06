from collections.abc import Callable
from time import perf_counter
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from pcfi_core.engine import PCFIEngine, DecisionOutcome
from pcfi_core.ir import Priority, PromptIR, Provenance, Segment
from pcfi_gateway.app.schemas.openai_compat import ChatCompletionRequest
from pcfi_gateway.app.telemetry import DECISION_COUNTER, LATENCY_HISTOGRAM


async def _build_prompt_ir_from_request(body_bytes: bytes) -> PromptIR:
    """
    Parse the incoming chat request into a PromptIR instance.

    At this stage we only distinguish:
    - system messages (SYSTEM priority)
    - user messages (USER priority)
    - rag_documents (RAG priority)
    """
    request = ChatCompletionRequest.model_validate_json(body_bytes)

    segments: list[Segment] = []

    for idx, msg in enumerate(request.messages):
        if msg.role == "system":
            priority = Priority.SYSTEM
        elif msg.role == "user":
            priority = Priority.USER
        else:
            # assistant messages are included for completeness but treated as USER-priority context.
            priority = Priority.USER

        provenance = Provenance(source="chat_message", index=idx, metadata={"role": msg.role})
        segments.append(
            Segment(
                text=msg.content,
                role=msg.role,  # type: ignore[arg-type]
                priority=priority,
                provenance=provenance,
            )
        )

    base_index = len(segments)
    for offset, doc in enumerate(request.rag_documents):
        provenance = Provenance(
            source="rag",
            index=base_index + offset,
            doc_id=doc.id,
            metadata={"source": doc.source, "score": doc.score},
        )
        segments.append(
            Segment(
                text=doc.content,
                role="rag",
                priority=Priority.RAG,
                provenance=provenance,
            )
        )

    return PromptIR(segments=segments)


_ENGINE = PCFIEngine()


async def pcfi_middleware(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """
    PCFI middleware entry point.

    Current responsibilities:
    - Parse chat completion requests into PromptIR and attach to `request.state`.
    - Measure and export middleware latency.

    Later phases will add the actual PCFI decision logic.
    """
    start = perf_counter()

    # Only intercept chat completion traffic for now.
    if request.method == "POST" and request.url.path.endswith("/chat/completions"):
        body_bytes = await request.body()
        prompt_ir = await _build_prompt_ir_from_request(body_bytes)
        decision = _ENGINE.run(prompt_ir)

        request.state.prompt_ir = prompt_ir
        request.state.pcfi_decision = decision

        # If PCFI decides to block, record metrics and short-circuit.
        if decision.outcome == DecisionOutcome.BLOCK:
            elapsed_ms = (perf_counter() - start) * 1000.0
            LATENCY_HISTOGRAM.observe(elapsed_ms)
            DECISION_COUNTER.labels(outcome=decision.outcome).inc()

            return JSONResponse(
                status_code=403,
                content={
                    "error": "Request blocked by PCFI",
                    "pcfi": decision.explanation,
                },
            )

        # Reconstruct the request so downstream handlers can read the body again.
        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        from starlette.requests import Request as StarletteRequest

        request = StarletteRequest(request.scope, receive=receive)

    response = await call_next(request)

    elapsed_ms = (perf_counter() - start) * 1000.0
    LATENCY_HISTOGRAM.observe(elapsed_ms)

    # If a decision was made for this request, update decision metrics.
    decision = getattr(request.state, "pcfi_decision", None)
    if decision is not None:
        DECISION_COUNTER.labels(outcome=decision.outcome).inc()

    return response

