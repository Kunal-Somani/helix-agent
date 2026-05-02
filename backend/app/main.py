"""FastAPI application entry point."""

from fastapi import FastAPI
from app.config import settings
from app.routes import quiz, metrics
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="LLM Quiz Solver",
    version="1.0.0",
    description="Production-grade LLM quiz solving system",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
)

# Register routes
app.include_router(quiz.router)
app.include_router(metrics.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(
        "app_startup",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("app_shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
