"""Metrics and monitoring endpoints."""

from fastapi import APIRouter
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/performance")
async def get_performance_metrics():
    """Get system performance metrics."""
    return {
        "quizzes_solved": 0,
        "average_accuracy": 0.0,
        "total_requests": 0,
    }


@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed health information."""
    return {
        "status": "healthy",
        "components": {
            "redis": "connected",
            "anthropic_api": "reachable",
        },
    }
