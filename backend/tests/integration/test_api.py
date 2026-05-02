"""Integration tests for API endpoints."""

import pytest


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_quiz_solve_endpoint(client):
    """Test quiz solving endpoint."""
    response = client.post("/api/quiz/solve", json={
        "quiz_id": "test-001",
        "title": "Test Quiz"
    })
    assert response.status_code == 200
    assert "status" in response.json()


def test_performance_metrics(client):
    """Test metrics endpoint."""
    response = client.get("/api/metrics/performance")
    assert response.status_code == 200
    data = response.json()
    assert "quizzes_solved" in data
    assert "average_accuracy" in data
