"""Test fixtures and configuration."""

import pytest
from app.config import settings
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    return settings


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_quiz_data():
    """Sample quiz for testing."""
    return {
        "quiz_id": "test-001",
        "title": "Sample Quiz",
        "questions": [
            {
                "id": "q1",
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4"
            }
        ]
    }
