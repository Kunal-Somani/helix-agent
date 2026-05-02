"""Pydantic models and request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    """Request to enqueue a quiz run via ARQ.
    
    Authentication is via Bearer token in Authorization header.
    """

    url: str = Field(..., description="Start URL of the quiz")


class IterationResponse(BaseModel):
    """Single iteration (step) in a quiz run."""

    step: int = Field(..., description="Iteration step number")
    url: str = Field(..., description="URL of this step")
    answer: str = Field(..., description="Answer submitted")
    correct: bool = Field(..., description="Whether answer was correct")
    next_url: Optional[str] = Field(None, description="Next URL if correct")
    explanation: str = Field(..., description="AI explanation of approach")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class RunResponse(BaseModel):
    """Complete quiz run response."""

    id: str = Field(..., description="Run ID")
    url: str = Field(..., description="Starting quiz URL")
    status: str = Field(..., description="Current status: queued|running|completed")
    final_status: Optional[str] = Field(
        None, description="Final status: success|failed|error"
    )
    started_at: str = Field(..., description="ISO 8601 start timestamp")
    completed_at: Optional[str] = Field(None, description="ISO 8601 completion timestamp")
    error: Optional[str] = Field(None, description="Error message if any")
    iterations: List[IterationResponse] = Field(
        default_factory=list, description="All iterations in this run"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status: ok")
    model: str = Field(..., description="LLM model name")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
