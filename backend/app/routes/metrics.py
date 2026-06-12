"""Metrics and monitoring endpoints."""

from fastapi import APIRouter
import structlog

from app.db import get_db

logger = structlog.get_logger()

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/performance")
async def get_performance_metrics():
    """Get system performance metrics."""
    conn = await get_db()
    
    total_runs_res = conn.execute("SELECT COUNT(*) FROM runs").fetchone()
    total_runs = total_runs_res[0] if total_runs_res else 0
    
    correct_res = conn.execute("SELECT COUNT(*) FROM iterations WHERE correct = 1").fetchone()
    correct_iters = correct_res[0] if correct_res else 0
    
    total_iters_res = conn.execute("SELECT COUNT(*) FROM iterations").fetchone()
    total_iters = total_iters_res[0] if total_iters_res else 0
    
    accuracy = (correct_iters / total_iters) if total_iters > 0 else 0.0
    
    return {
        "quizzes_solved": total_runs,
        "average_accuracy": round(accuracy, 4),
        "total_requests": total_iters,
    }
