"""FastAPI application entry point with Prometheus metrics, rate limiting, and structured logging."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.logger import setup_logging, log
from app.routes import quiz, metrics


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# Prometheus metrics
QUIZ_RUNS_TOTAL = Counter(
    "quiz_runs_total",
    "Total quiz runs enqueued",
    ["environment"],
)
QUIZ_SUCCESS_TOTAL = Counter(
    "quiz_success_total",
    "Total quiz runs completed successfully",
)
QUIZ_FAILED_TOTAL = Counter(
    "quiz_failed_total",
    "Total quiz runs failed or errored",
)
AGENT_LLM_LATENCY = Histogram(
    "agent_llm_latency_seconds",
    "Anthropic API call latency",
    ["call_type"],
)
SANDBOX_EXEC_LATENCY = Histogram(
    "sandbox_exec_latency_seconds",
    "Code sandbox execution latency in seconds",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    setup_logging(settings.LOG_LEVEL)
    log.info("app.startup", environment=settings.ENVIRONMENT, version="2.0.0")
    yield
    # Shutdown
    log.info("app.shutdown")


app = FastAPI(
    title="Helix",
    version="2.0.0",
    description="Autonomous agentic system for recursive web task solving",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: {
    "error": "Rate limit exceeded",
    "detail": str(exc.detail)
})

# Attach Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Register routes
app.include_router(quiz.router)
app.include_router(metrics.router)


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth, no rate limit)."""
    return {
        "status": "ok",
        "model": "claude-sonnet-4-20250514",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
