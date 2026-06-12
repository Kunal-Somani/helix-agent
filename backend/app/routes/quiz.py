"""Quiz endpoint handlers with rate limiting and history tracking."""

from datetime import datetime
from uuid import uuid4


from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import asyncio

from app.config import settings
from app.logger import log
from app.main import limiter
from app.middleware.auth import verify_api_key
from app.models.schemas import QuizRequest, RunResponse
from app.services.agent import solve_quiz_task
from app.services.browser import get_task_from_url
from app.services import history as run_history
from app.services.sandbox import execute_python_code

router = APIRouter(prefix="/api/quiz", tags=["quiz"])



@router.get("/runs", response_model=list[RunResponse])
@limiter.limit("60/minute")
async def list_runs(request: Request):
    """List all quiz runs (newest first).
    
    Returns paginated list of all quiz runs with their iterations.
    No authentication required (read-only).
    Rate limited to 60/minute.
    
    Returns:
        List of RunResponse objects
    """
    try:
        runs = await run_history.get_all()
        log.info("history.list_runs", count=len(runs))
        return runs
    except Exception as e:
        log.error("history.list_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve runs")


@router.get("/runs/{run_id}", response_model=RunResponse)
@limiter.limit("60/minute")
async def get_run(request: Request, run_id: str):
    """Retrieve a single quiz run by ID.
    
    Returns complete run record including all iterations.
    No authentication required (read-only).
    Rate limited to 60/minute.
    
    Args:
        run_id: The run ID (UUID)
        
    Returns:
        RunResponse object
        
    Raises:
        404: If run not found
    """
    try:
        run = await run_history.get_run(run_id)
        
        if not run:
            log.warning("history.run_not_found", run_id=run_id)
            raise HTTPException(status_code=404, detail="Run not found")
        
        log.info("history.run_retrieved", run_id=run_id, iterations=len(run.get("iterations", [])))
        return run
    except HTTPException:
        raise
    except Exception as e:
        log.error("history.get_error", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve run")


@router.post("/run", response_model=dict)
@limiter.limit("10/minute")
async def run_quiz(
    request: Request,
    body: QuizRequest,
    api_key: str = Depends(verify_api_key),
):
    """Enqueue a complete quiz run (multi-step flow) via ARQ.
    
    This endpoint:
    1. Validates Bearer token in Authorization header
    2. Creates a run record in history
    3. Enqueues the process_quiz_flow task to ARQ
    4. Returns immediately with the run_id for tracking
    
    The actual processing happens asynchronously in the worker.
    
    Authentication:
        Bearer <api_key> in Authorization header (required)
    
    Rate limit:
        10 per minute per IP
    
    Args:
        body: QuizRequest with url field
        api_key: Validated Bearer token from Authorization header
        
    Returns:
        Dictionary with run_id for tracking progress
        
    Raises:
        401: Invalid or missing API key
        429: Rate limit exceeded
        500: Failed to enqueue job
    """
    try:
        run_id = str(uuid4())
        log.info("quiz.run_requested", run_id=run_id, url=body.url)

        # Create run record in history
        await run_history.create_run(run_id, body.url)

        from app.worker import enqueue_run
        enqueue_run(body.url, run_id)

        log.info("quiz.run_enqueued", run_id=run_id)

        return {
            "message": "Quiz run enqueued",
            "run_id": run_id,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log.error("quiz.run_error", error=str(e))
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
        run = await run_history.get_run(run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        log.info("quiz_status_retrieved", run_id=run_id, status=run.get("status"))
        
        return run
    except HTTPException:
        raise
    except Exception as e:
        log.error("quiz_status_error", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/logs")
async def stream_logs(run_id: str):
    async def event_generator():
        last_count = 0
        for _ in range(120):
            run = await run_history.get_run(run_id)
            if run:
                iterations = run.get("iterations", [])
                if len(iterations) > last_count:
                    for it in iterations[last_count:]:
                        line = f"[Step {it['step']}] {it['explanation']} | Answer: {it['answer']} | Correct: {it['correct']}"
                        yield f"data: {line}\n\n"
                    last_count = len(iterations)
                if run.get("status") == "completed":
                    yield f"data: [DONE] Run completed with status: {run.get('final_status')}\n\n"
                    break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })
