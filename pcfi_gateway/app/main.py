from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .middleware.pcfi import pcfi_middleware
from .settings import Settings


settings = Settings()

app = FastAPI(
    title="PCFI Gateway",
    version="0.1.0",
    description="Prompt Control-Flow Integrity gateway for Groq-backed LLMs.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# PCFI middleware wraps all API requests that reach the LLM backends.
app.middleware("http")(pcfi_middleware)

app.include_router(api_router, prefix="/v1")

