"""ARQ worker for persistent, retriable background task processing.

Handles the complete quiz flow:
1. Fetch task from URL
2. Extract task information (submission URL, problem description)
3. Generate and execute solution code
4. Submit answer
5. Repeat if correct with next URL
6. Track history and results
"""

import asyncio
from datetime import datetime

import requests
from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.logger import log
from app.services.agent import solve_quiz_task
from app.services.browser import get_task_from_url
from app.services.history import history_service
from app.services.sandbox import execute_python_code


async def process_quiz_flow(ctx, start_url: str, run_id: str):
    """Process a complete quiz flow with multiple iterations.
    
    This is the main ARQ task that:
    1. Retrieves task information from the URL
    2. Generates Python solution code using Claude
    3. Executes the code to get the answer
    4. Submits the answer to the submission endpoint
    5. Follows to next URL if correct
    6. Repeats up to 5 times
    7. Tracks all iterations in history
    
    Args:
        ctx: ARQ job context (provides job info, etc.)
        start_url: Initial quiz URL
        run_id: Unique identifier for this quiz run
        
    Returns:
        Dictionary with final status and completion info
    """
    current_url = start_url
    await history_service.update_run(run_id, status="running")

    for i in range(5):
        log.info("worker.iteration", run_id=run_id, url=current_url, step=i + 1)

        try:
            # Step 1: Fetch task from URL
            task_text = await get_task_from_url(current_url)

            # Step 2: Extract task info and generate code
            submission_url, python_code, explanation = solve_quiz_task(
                task_text, current_url
            )

            # Step 3: Execute generated code in sandbox
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None, execute_python_code, python_code
            )

            # Step 4: Prepare submission payload
            payload = {
                "email": settings.MY_EMAIL,
                "secret": settings.MY_SECRET,
                "url": current_url,
                "answer": answer,
            }

            log.info(
                "worker.submitting",
                run_id=run_id,
                url=submission_url,
                answer=str(answer)[:100],
            )

            # Step 5: Submit answer
            resp = requests.post(submission_url, json=payload, timeout=15)
            res_json = resp.json()
            correct = res_json.get("correct", False)
            next_url = res_json.get("url") if correct else None

            # Step 6: Record iteration in history
            await history_service.add_iteration(
                run_id,
                {
                    "step": i + 1,
                    "url": current_url,
                    "answer": str(answer),
                    "correct": correct,
                    "next_url": next_url,
                    "explanation": explanation,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            log.info(
                "worker.result", run_id=run_id, correct=correct, next_url=next_url
            )

            # Step 7: Determine next action
            if correct and next_url:
                # Continue to next quiz
                current_url = next_url
            elif correct and not next_url:
                # Successfully completed all quizzes
                await history_service.update_run(
                    run_id,
                    status="completed",
                    final_status="success",
                    completed_at=datetime.utcnow().isoformat(),
                )
                log.info("worker.done", run_id=run_id)
                break
            else:
                # Answer was incorrect, stop processing
                await history_service.update_run(
                    run_id,
                    status="completed",
                    final_status="failed",
                    completed_at=datetime.utcnow().isoformat(),
                )
                log.info("worker.failed", run_id=run_id, step=i + 1)
                break

        except Exception as e:
            log.error(
                "worker.error",
                run_id=run_id,
                step=i + 1,
                error=str(e),
                error_type=type(e).__name__,
            )
            await history_service.update_run(
                run_id,
                status="completed",
                final_status="error",
                error=str(e),
                completed_at=datetime.utcnow().isoformat(),
            )
            break

    return {"run_id": run_id, "status": "completed"}


class WorkerSettings:
    """ARQ worker configuration.
    
    Configures:
    - functions: Tuple of async functions to register as tasks
    - redis_settings: Redis connection details from DSN
    - max_jobs: Maximum concurrent jobs
    - job_timeout: Maximum seconds a job can run
    - keep_result: Seconds to keep job results in Redis
    """

    functions = [process_quiz_flow]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300  # 5 minutes per job
    keep_result = 3600  # Keep results for 1 hour


async def startup(ctx):
    """Worker startup hook."""
    log.info("worker_startup", environment=settings.ENVIRONMENT, redis=settings.REDIS_URL)


async def shutdown(ctx):
    """Worker shutdown hook."""
    log.info("worker_shutdown")
