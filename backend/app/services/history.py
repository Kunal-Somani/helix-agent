"""Thread-safe async run history service.

Provides in-memory FIFO storage for quiz runs with asyncio.Lock
for concurrent access safety.
In production, this should use Redis or PostgreSQL.
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import List, Optional

from app.logger import log


class RunHistory:
    """Thread-safe in-memory store for quiz run history.
    
    Uses asyncio.Lock for concurrent access.
    Stores runs in FIFO order (newest first via appendleft).
    Maxlen=200 keeps only the 200 most recent runs.
    """

    def __init__(self, maxlen: int = 200):
        """Initialize run history store.
        
        Args:
            maxlen: Maximum number of runs to keep (FIFO eviction)
        """
        self._runs: deque = deque(maxlen=maxlen)
        self._lock = asyncio.Lock()

    async def create_run(self, run_id: str, url: str) -> dict:
        """Create a new quiz run record.
        
        Args:
            run_id: Unique identifier for this run
            url: Starting URL for the quiz
            
        Returns:
            The created run dictionary
        """
        run = {
            "id": run_id,
            "url": url,
            "status": "queued",
            "final_status": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "iterations": [],
        }
        
        async with self._lock:
            self._runs.appendleft(run)
        
        log.info("history.run_created", run_id=run_id, url=url)
        return run

    async def update_run(self, run_id: str, **kwargs) -> None:
        """Update run fields.
        
        Args:
            run_id: The run identifier
            **kwargs: Fields to update (status, final_status, completed_at, error)
        """
        async with self._lock:
            for run in self._runs:
                if run["id"] == run_id:
                    run.update(kwargs)
                    log.info(
                        "history.run_updated",
                        run_id=run_id,
                        status=kwargs.get("status"),
                        final_status=kwargs.get("final_status"),
                    )
                    return
        
        log.warning("history.run_not_found", run_id=run_id)

    async def add_iteration(self, run_id: str, data: dict) -> None:
        """Record an iteration (quiz attempt step).
        
        Args:
            run_id: The run identifier
            data: Iteration data (step, url, answer, correct, explanation, timestamp)
        """
        async with self._lock:
            for run in self._runs:
                if run["id"] == run_id:
                    run["iterations"].append(data)
                    log.info(
                        "history.iteration_recorded",
                        run_id=run_id,
                        step=data.get("step"),
                        correct=data.get("correct"),
                    )
                    return
        
        log.warning("history.run_not_found", run_id=run_id)

    async def get_all(self) -> List[dict]:
        """Retrieve all runs in FIFO order (newest first).
        
        Returns:
            List of run dictionaries
        """
        async with self._lock:
            return list(self._runs)

    async def get_run(self, run_id: str) -> Optional[dict]:
        """Retrieve a single run by ID.
        
        Args:
            run_id: The run identifier
            
        Returns:
            Run dictionary if found, None otherwise
        """
        async with self._lock:
            for run in self._runs:
                if run["id"] == run_id:
                    return run
        
        return None


# Global singleton instance
run_history = RunHistory()
            return {"total_runs": 0, "completed": 0, "success": 0, "failed": 0}

        completed = sum(
            1 for r in self.runs.values() if r["status"] == "completed"
        )
        success = sum(
            1 for r in self.runs.values()
            if r.get("final_status") == "success"
        )
        failed = sum(
            1 for r in self.runs.values()
            if r.get("final_status") == "failed"
        )

        return {
            "total_runs": len(self.runs),
            "total_iterations": sum(len(iters) for iters in self.iterations.values()),
            "completed": completed,
            "success": success,
            "failed": failed,
            "in_progress": sum(
                1 for r in self.runs.values() if r["status"] == "running"
            ),
        }


# Global instance
history_service = HistoryService()
