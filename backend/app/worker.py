"""Worker for background task processing.

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

from app.config import settings
from app.logger import log
from app.main import (
    QUIZ_RUNS_TOTAL,
    QUIZ_SUCCESS_TOTAL,
    QUIZ_FAILED_TOTAL,
    SANDBOX_EXEC_LATENCY,
)
from app.services.agent import solve_quiz_task
from app.services.browser import get_task_from_url
from app.services import history as run_history
from app.services.sandbox import execute_python_code


async def run_quiz_flow(start_url: str, run_id: str):
    current_url = start_url
    await run_history.update_run(run_id, status="running")
    
    QUIZ_RUNS_TOTAL.labels(environment=settings.ENVIRONMENT).inc()
    log.info("worker.job_start", run_id=run_id, start_url=start_url)

    for i in range(5):
        log.info("worker.iteration", run_id=run_id, url=current_url, step=i + 1)

        try:
            task_text = await get_task_from_url(current_url)

            loop = asyncio.get_event_loop()
            submission_url, python_code, explanation = await loop.run_in_executor(
                None, solve_quiz_task, task_text, current_url
            )

            with SANDBOX_EXEC_LATENCY.time():
                answer = await loop.run_in_executor(
                    None, execute_python_code, python_code
                )

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

            resp = requests.post(submission_url, json=payload, timeout=15)
            res_json = resp.json()
            correct = res_json.get("correct", False)
            next_url = res_json.get("url") if correct else None

            await run_history.add_iteration(
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

            if correct and next_url:
                current_url = next_url
            elif correct and not next_url:
                await run_history.update_run(
                    run_id,
                    status="completed",
                    final_status="success",
                    completed_at=datetime.utcnow().isoformat(),
                )
                QUIZ_SUCCESS_TOTAL.inc()
                log.info("worker.done", run_id=run_id, status="success")
                break
            else:
                await run_history.update_run(
                    run_id,
                    status="completed",
                    final_status="failed",
                    completed_at=datetime.utcnow().isoformat(),
                )
                QUIZ_FAILED_TOTAL.inc()
                log.info("worker.failed", run_id=run_id, step=i + 1, status="failed")
                break

        except Exception as e:
            log.error(
                "worker.error",
                run_id=run_id,
                step=i + 1,
                error=str(e),
                error_type=type(e).__name__,
            )
            await run_history.update_run(
                run_id,
                status="completed",
                final_status="error",
                error=str(e),
                completed_at=datetime.utcnow().isoformat(),
            )
            QUIZ_FAILED_TOTAL.inc()
            break

    return {"run_id": run_id, "status": "completed"}


def enqueue_run(start_url: str, run_id: str):
    asyncio.create_task(run_quiz_flow(start_url, run_id))
