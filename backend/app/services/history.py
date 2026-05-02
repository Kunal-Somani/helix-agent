"""Quiz solving history and persistence service.

Tracks quiz run progress, iterations, and results.
In production, this should use a real database (PostgreSQL, MongoDB).
Currently uses in-memory storage with async support.
"""

from datetime import datetime
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()


class HistoryService:
    """Manage quiz solving history and run tracking.
    
    Stores:
    - Run metadata (id, url, status, timestamps)
    - Iterations (steps, answers, correctness)
    - Final results and errors
    """

    def __init__(self):
        self.runs: Dict[str, dict] = {}
        self.iterations: Dict[str, List[dict]] = {}

    async def create_run(self, run_id: str, start_url: str) -> None:
        """Create a new quiz run record.
        
        Args:
            run_id: Unique identifier for this run
            start_url: Initial quiz URL
        """
        self.runs[run_id] = {
            "run_id": run_id,
            "start_url": start_url,
            "status": "queued",
            "final_status": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        self.iterations[run_id] = []
        logger.info("run_created", run_id=run_id, url=start_url)

    async def update_run(
        self,
        run_id: str,
        status: str,
        final_status: Optional[str] = None,
        completed_at: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update run status.
        
        Args:
            run_id: The run identifier
            status: Current status (queued, running, completed)
            final_status: Final outcome (success, failed, error)
            completed_at: Timestamp when run completed
            error: Error message if applicable
        """
        if run_id not in self.runs:
            return

        self.runs[run_id]["status"] = status

        if status == "running" and not self.runs[run_id]["started_at"]:
            self.runs[run_id]["started_at"] = datetime.utcnow().isoformat()

        if final_status:
            self.runs[run_id]["final_status"] = final_status

        if completed_at:
            self.runs[run_id]["completed_at"] = completed_at

        if error:
            self.runs[run_id]["error"] = error

        logger.info(
            "run_updated",
            run_id=run_id,
            status=status,
            final_status=final_status,
        )

    async def add_iteration(self, run_id: str, iteration_data: dict) -> None:
        """Record a single quiz attempt iteration.
        
        Args:
            run_id: The run identifier
            iteration_data: Dictionary with step, url, answer, correct, etc.
        """
        if run_id not in self.iterations:
            self.iterations[run_id] = []

        self.iterations[run_id].append(iteration_data)
        logger.info(
            "iteration_recorded",
            run_id=run_id,
            step=iteration_data.get("step"),
            correct=iteration_data.get("correct"),
        )

    async def get_run(self, run_id: str) -> Optional[Dict]:
        """Retrieve a complete run record with all iterations.
        
        Args:
            run_id: The run identifier
            
        Returns:
            Dictionary with run metadata and iterations, or None if not found
        """
        if run_id not in self.runs:
            return None

        run = self.runs[run_id].copy()
        run["iterations"] = self.iterations.get(run_id, [])
        return run

    async def get_history(self, run_id: Optional[str] = None) -> List[dict]:
        """Retrieve quiz solving history.
        
        Args:
            run_id: Optional specific run to retrieve. If None, returns all.
            
        Returns:
            List of run records
        """
        if run_id:
            run = await self.get_run(run_id)
            return [run] if run else []
        return [self._build_run_record(rid) for rid in self.runs.keys()]

    def _build_run_record(self, run_id: str) -> dict:
        """Build a complete run record with iterations."""
        run = self.runs[run_id].copy()
        run["iterations"] = self.iterations.get(run_id, [])
        return run

    async def get_statistics(self) -> dict:
        """Get overall statistics across all runs.
        
        Returns:
            Dictionary with counts and metrics
        """
        if not self.runs:
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
