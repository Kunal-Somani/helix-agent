"""FastAPI application entry point with Prometheus metrics, rate limiting, and structured logging."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    
    from app.db import init_db
    await init_db()
    
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

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "detail": str(exc.detail)}
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

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
