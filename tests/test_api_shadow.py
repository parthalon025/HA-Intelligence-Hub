"""Tests for shadow engine API endpoints."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from hub.api import create_api
from hub.core import IntelligenceHub


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def hub():
    """Create a mock hub for API tests."""
    mock_hub = MagicMock(spec=IntelligenceHub)
    mock_hub.cache = MagicMock()
    mock_hub.modules = {}
    mock_hub.subscribers = {}
    mock_hub.subscribe = MagicMock()
    return mock_hub


@pytest.fixture
def client(hub):
    """Create test client with mock hub."""
    app = create_api(hub)
    return TestClient(app)


# ============================================================================
# GET /api/shadow/predictions
# ============================================================================


class TestGetPredictions:

    def test_get_predictions_empty(self, hub, client):
        """Returns empty list when no predictions exist."""
        hub.cache.get_recent_predictions = AsyncMock(return_value=[])

        response = client.get("/api/shadow/predictions")
        assert response.status_code == 200

        data = response.json()
        assert data["predictions"] == []
        assert data["count"] == 0

    def test_get_predictions_with_data(self, hub, client):
        """Returns predictions with correct format."""
        predictions = [
            {
                "id": "pred-001",
                "timestamp": "2026-02-12T10:00:00",
                "context": {"room": "living_room"},
                "predictions": [{"action": "light.turn_on"}],
                "outcome": "correct",
                "actual": {"event": "light.turn_on"},
                "confidence": 0.85,
                "is_exploration": False,
                "propagated_count": 0,
                "window_seconds": 300,
                "resolved_at": "2026-02-12T10:05:00",
            },
            {
                "id": "pred-002",
                "timestamp": "2026-02-12T09:00:00",
                "context": {"room": "kitchen"},
                "predictions": [{"action": "light.turn_off"}],
                "outcome": "disagreement",
                "actual": None,
                "confidence": 0.60,
                "is_exploration": False,
                "propagated_count": 0,
                "window_seconds": 300,
                "resolved_at": "2026-02-12T09:05:00",
            },
        ]
        hub.cache.get_recent_predictions = AsyncMock(return_value=predictions)

        response = client.get("/api/shadow/predictions")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 2
        assert data["predictions"][0]["id"] == "pred-001"
        assert data["predictions"][1]["id"] == "pred-002"

    def test_get_predictions_pagination(self, hub, client):
        """Limit and offset params are passed through."""
        hub.cache.get_recent_predictions = AsyncMock(return_value=[])

        client.get("/api/shadow/predictions?limit=10&offset=5")

        hub.cache.get_recent_predictions.assert_called_once_with(limit=10, offset=5)

    def test_get_predictions_error(self, hub, client):
        """Returns 500 on cache error."""
        hub.cache.get_recent_predictions = AsyncMock(side_effect=RuntimeError("db error"))

        response = client.get("/api/shadow/predictions")
        assert response.status_code == 500


# ============================================================================
# GET /api/shadow/accuracy
# ============================================================================


class TestGetAccuracy:

    def test_get_accuracy_empty(self, hub, client):
        """Returns zeroes when no data exists."""
        hub.cache.get_accuracy_stats = AsyncMock(return_value={
            "overall_accuracy": 0.0,
            "total_resolved": 0,
            "per_outcome": {},
            "daily_trend": [],
        })
        hub.cache.get_pipeline_state = AsyncMock(return_value={
            "current_stage": "backtest",
            "stage_entered_at": "2026-02-12T00:00:00",
            "updated_at": "2026-02-12T00:00:00",
        })

        response = client.get("/api/shadow/accuracy")
        assert response.status_code == 200

        data = response.json()
        assert data["overall_accuracy"] == 0.0
        assert data["predictions_total"] == 0
        assert data["predictions_correct"] == 0
        assert data["predictions_disagreement"] == 0
        assert data["predictions_nothing"] == 0
        assert data["by_type"] == {}
        assert data["stage"] == "backtest"

    def test_get_accuracy_with_stats(self, hub, client):
        """Returns accuracy breakdown with correct mapping."""
        hub.cache.get_accuracy_stats = AsyncMock(return_value={
            "overall_accuracy": 0.75,
            "total_resolved": 20,
            "per_outcome": {
                "correct": 15,
                "disagreement": 3,
                "nothing": 2,
            },
            "daily_trend": [
                {"date": "2026-02-12", "correct": 15, "total": 20, "accuracy": 0.75},
            ],
        })
        hub.cache.get_pipeline_state = AsyncMock(return_value={
            "current_stage": "shadow",
            "stage_entered_at": "2026-02-10T00:00:00",
            "updated_at": "2026-02-12T00:00:00",
        })

        response = client.get("/api/shadow/accuracy")
        assert response.status_code == 200

        data = response.json()
        assert data["overall_accuracy"] == 0.75
        assert data["predictions_total"] == 20
        assert data["predictions_correct"] == 15
        assert data["predictions_disagreement"] == 3
        assert data["predictions_nothing"] == 2
        assert data["stage"] == "shadow"
        assert len(data["daily_trend"]) == 1

    def test_get_accuracy_error(self, hub, client):
        """Returns 500 on cache error."""
        hub.cache.get_accuracy_stats = AsyncMock(side_effect=RuntimeError("db error"))

        response = client.get("/api/shadow/accuracy")
        assert response.status_code == 500


# ============================================================================
# GET /api/shadow/disagreements
# ============================================================================


class TestGetDisagreements:

    def test_get_disagreements_empty(self, hub, client):
        """Returns empty list when no disagreements exist."""
        hub.cache.get_recent_predictions = AsyncMock(return_value=[])

        response = client.get("/api/shadow/disagreements")
        assert response.status_code == 200

        data = response.json()
        assert data["disagreements"] == []
        assert data["count"] == 0

    def test_get_disagreements_sorted_by_confidence(self, hub, client):
        """Returns disagreements sorted by confidence descending."""
        disagreements = [
            {"id": "p1", "confidence": 0.5, "outcome": "disagreement"},
            {"id": "p2", "confidence": 0.9, "outcome": "disagreement"},
            {"id": "p3", "confidence": 0.7, "outcome": "disagreement"},
        ]
        hub.cache.get_recent_predictions = AsyncMock(return_value=disagreements)

        response = client.get("/api/shadow/disagreements")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 3
        # Highest confidence first
        assert data["disagreements"][0]["id"] == "p2"
        assert data["disagreements"][1]["id"] == "p3"
        assert data["disagreements"][2]["id"] == "p1"

    def test_get_disagreements_respects_limit(self, hub, client):
        """Limit param caps the number of returned disagreements."""
        disagreements = [
            {"id": f"p{i}", "confidence": i * 0.1, "outcome": "disagreement"}
            for i in range(10)
        ]
        hub.cache.get_recent_predictions = AsyncMock(return_value=disagreements)

        response = client.get("/api/shadow/disagreements?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 3

    def test_get_disagreements_uses_outcome_filter(self, hub, client):
        """Verifies the cache call uses outcome_filter='disagreement'."""
        hub.cache.get_recent_predictions = AsyncMock(return_value=[])

        client.get("/api/shadow/disagreements")

        hub.cache.get_recent_predictions.assert_called_once_with(
            limit=200, outcome_filter="disagreement"
        )

    def test_get_disagreements_error(self, hub, client):
        """Returns 500 on cache error."""
        hub.cache.get_recent_predictions = AsyncMock(side_effect=RuntimeError("db error"))

        response = client.get("/api/shadow/disagreements")
        assert response.status_code == 500


# ============================================================================
# GET /api/pipeline
# ============================================================================


class TestGetPipeline:

    def test_get_pipeline_not_initialized(self, hub, client):
        """Returns default state when pipeline is None."""
        hub.cache.get_pipeline_state = AsyncMock(return_value=None)

        response = client.get("/api/pipeline")
        assert response.status_code == 200

        data = response.json()
        assert data["current_stage"] == "shadow"
        assert data["gates"] == {}
        assert "message" in data

    def test_get_pipeline_with_state(self, hub, client):
        """Returns full pipeline state when initialized."""
        pipeline = {
            "id": 1,
            "current_stage": "shadow",
            "stage_entered_at": "2026-02-10T00:00:00",
            "backtest_accuracy": 0.92,
            "shadow_accuracy_7d": 0.85,
            "suggest_approval_rate_14d": None,
            "autonomous_contexts": None,
            "updated_at": "2026-02-12T10:00:00",
        }
        hub.cache.get_pipeline_state = AsyncMock(return_value=pipeline)

        response = client.get("/api/pipeline")
        assert response.status_code == 200

        data = response.json()
        assert data["current_stage"] == "shadow"
        assert data["backtest_accuracy"] == 0.92
        assert data["shadow_accuracy_7d"] == 0.85
        assert data["updated_at"] == "2026-02-12T10:00:00"

    def test_get_pipeline_error(self, hub, client):
        """Returns 500 on cache error."""
        hub.cache.get_pipeline_state = AsyncMock(side_effect=RuntimeError("db error"))

        response = client.get("/api/pipeline")
        assert response.status_code == 500
