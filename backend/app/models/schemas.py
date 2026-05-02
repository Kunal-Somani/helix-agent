"""Pydantic models and request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """Single quiz question."""

    id: str
    text: str
    options: List[str]
    correct_answer: Optional[str] = None


class QuizRequest(BaseModel):
    """Request to start a quiz run.
    
    Can be used for:
    - /api/quiz/solve - Synchronous single task solving
    - /api/quiz/run - Asynchronous multi-step flow via ARQ
    """

    url: str = Field(..., description="Start URL of the quiz")
    title: Optional[str] = Field(None, description="Optional quiz title")
    questions: Optional[List[QuizQuestion]] = Field(
        None, description="Optional pre-extracted questions"
    )


class QuizResponse(BaseModel):
    """Response with quiz solutions."""

    quiz_id: str
    status: str
    solutions: Optional[dict] = None
    accuracy: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuizRunResponse(BaseModel):
    """Response when enqueueing a quiz run to ARQ."""

    message: str
    run_id: str
    job_id: Optional[str] = None
    status: str = "queued"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
