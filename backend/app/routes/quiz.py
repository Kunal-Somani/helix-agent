"""Quiz endpoint handlers."""

from datetime import datetime
from uuid import uuid4

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.logger import log
from app.middleware.auth import verify_api_key
from app.models.schemas import QuizRequest
from app.services.agent import solve_quiz_task
from app.services.history import history_service
from app.services.sandbox import execute_python_code

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Simple rate limiter (production should use slowapi or equivalent)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def execute_python_code_wrapped(python_code: str) -> dict:
    """Execute generated Python code safely.
    
    Args:
        python_code: Python code with 'result' variable assigned
        
    Returns:
        Dictionary with 'result' key containing the execution result
        
    Raises:
        Exception: If code execution fails
    """
    namespace = {}
    try:
        exec(python_code, namespace)
        result = namespace.get("result")
        log.info("code_execution_success", result_type=type(result).__name__)
        return {"result": result}
    except Exception as e:
        log.error("code_execution_failed", error=str(e))
        raise


@router.post("/solve")
@limiter.limit("10/minute")
async def solve_quiz(
    request: Request,
    task_text: str,
    current_url: str,
    api_key: str = Depends(verify_api_key),
):
    """Solve quiz task synchronously: extract info and generate solution code.
    
    Query Parameters:
        task_text: Raw HTML/text content of the task page
        current_url: Current page URL for context
        
    Returns:
        JSON with submission_url, python_code, explanation, and result
    """
    try:
        log.info("quiz_solve_requested", url=current_url)

        # Orchestrate task solving (extraction + code generation)
        submission_url, python_code, explanation = solve_quiz_task(
            task_text, current_url
        )

        # Execute the generated code
        execution_result = execute_python_code_wrapped(python_code)
        answer = execution_result["result"]

        log.info(
            "quiz_solve_completed",
            submission_url=submission_url,
            answer=str(answer)[:100],
        )

        return {
            "status": "solved",
            "submission_url": submission_url,
            "python_code": python_code,
            "explanation": explanation,
            "result": answer,
        }
    except Exception as e:
        log.error("quiz_solve_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
@limiter.limit("5/minute")
async def run_quiz(
    request: Request,
    body: QuizRequest,
    api_key: str = Depends(verify_api_key),
):
    """Enqueue a complete quiz run (multi-step flow) via ARQ.
    
    This endpoint:
    1. Creates a run record in history
    2. Enqueues the process_quiz_flow task to ARQ
    3. Returns immediately with the run_id for tracking
    
    The actual processing happens asynchronously in the worker.
    
    Args:
        body: QuizRequest with url field
        api_key: API key from Authorization header
        
    Returns:
        Dictionary with run_id for tracking progress
    """
    try:
        run_id = str(uuid4())
        log.info("quiz_run_requested", run_id=run_id, url=body.url)

        # Create run record in history
        await history_service.create_run(run_id, body.url)

        # Connect to Redis and enqueue job
        redis = await create_pool(
            RedisSettings.from_dsn(settings.REDIS_URL)
        )
        
        job = await redis.enqueue_job("process_quiz_flow", body.url, run_id)
        
        await redis.close()

        log.info("quiz_run_enqueued", run_id=run_id, job_id=job.job_id)

        return {
            "message": "Quiz run enqueued",
            "run_id": run_id,
            "job_id": job.job_id,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log.error("quiz_run_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to enqueue quiz run: {str(e)}"
        )


@router.get("/status/{run_id}")
@limiter.limit("20/minute")
async def get_quiz_status(
    request: Request,
    run_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get the status and results of a quiz run.
    
    Args:
        run_id: The run ID returned from /run endpoint
        api_key: API key from Authorization header
        
    Returns:
        Dictionary with run status, iterations, and final result
    """
    try:
        run = await history_service.get_run(run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        log.info("quiz_status_retrieved", run_id=run_id, status=run.get("status"))
        
        return run
    except HTTPException:
        raise
    except Exception as e:
        log.error("quiz_status_error", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
