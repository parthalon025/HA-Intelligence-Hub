"""Tests for organic discovery API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_discovery_module():
    """Create a mock organic discovery module."""
    module = MagicMock()
    module.settings = {
        "autonomy_mode": "suggest_and_wait",
        "naming_backend": "heuristic",
        "promote_threshold": 50,
        "archive_threshold": 10,
        "promote_streak_days": 7,
        "archive_streak_days": 14,
    }
    module.history = []
    module.run_discovery = AsyncMock()
    module.update_settings = AsyncMock()
    return module


# ============================================================================
# GET /api/capabilities/candidates
# ============================================================================


class TestGetCapabilityCandidates:
    def test_returns_only_candidates(self, api_hub, api_client):
        """Returns only capabilities with status=candidate."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "lighting_control": {"status": "promoted", "source": "seed"},
                "climate_sensors": {"status": "candidate", "source": "organic"},
                "motion_tracking": {"status": "archived", "source": "organic"},
                "power_monitoring": {"status": "candidate", "source": "organic"},
            }
        })

        response = api_client.get("/api/capabilities/candidates")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert "climate_sensors" in data
        assert "power_monitoring" in data
        assert "lighting_control" not in data
        assert "motion_tracking" not in data

    def test_returns_empty_when_no_cache(self, api_hub, api_client):
        """Returns empty dict when capabilities not cached."""
        api_hub.cache.get = AsyncMock(return_value=None)

        response = api_client.get("/api/capabilities/candidates")
        assert response.status_code == 200
        assert response.json() == {}

    def test_returns_empty_when_no_data(self, api_hub, api_client):
        """Returns empty dict when cache has no data field."""
        api_hub.cache.get = AsyncMock(return_value={"data": None})

        response = api_client.get("/api/capabilities/candidates")
        assert response.status_code == 200
        assert response.json() == {}

    def test_returns_empty_when_no_candidates(self, api_hub, api_client):
        """Returns empty dict when all capabilities are promoted or archived."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "lighting_control": {"status": "promoted"},
                "motion_tracking": {"status": "archived"},
            }
        })

        response = api_client.get("/api/capabilities/candidates")
        assert response.status_code == 200
        assert response.json() == {}


# ============================================================================
# GET /api/capabilities/history
# ============================================================================


class TestGetDiscoveryHistory:
    def test_returns_history_list(self, api_hub, api_client):
        """Returns discovery history from cache."""
        history = [
            {"timestamp": "2026-02-14", "clusters_found": 5, "total_merged": 12},
            {"timestamp": "2026-02-13", "clusters_found": 4, "total_merged": 11},
        ]
        api_hub.cache.get = AsyncMock(return_value={"data": history})

        response = api_client.get("/api/capabilities/history")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["timestamp"] == "2026-02-14"
        assert data[0]["clusters_found"] == 5

    def test_returns_empty_when_no_cache(self, api_hub, api_client):
        """Returns empty list when no history cached."""
        api_hub.cache.get = AsyncMock(return_value=None)

        response = api_client.get("/api/capabilities/history")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_empty_when_no_data(self, api_hub, api_client):
        """Returns empty list when cache has no data field."""
        api_hub.cache.get = AsyncMock(return_value={"data": None})

        response = api_client.get("/api/capabilities/history")
        assert response.status_code == 200
        assert response.json() == []


# ============================================================================
# PUT /api/capabilities/{name}/promote
# ============================================================================


class TestPromoteCapability:
    def test_promotes_capability(self, api_hub, api_client):
        """Promotes a candidate capability and returns 200."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "climate_sensors": {"status": "candidate", "source": "organic"},
            }
        })
        api_hub.cache.set = AsyncMock()

        response = api_client.put("/api/capabilities/climate_sensors/promote")
        assert response.status_code == 200

        data = response.json()
        assert data["capability"] == "climate_sensors"
        assert data["status"] == "promoted"

        # Verify cache was updated
        api_hub.cache.set.assert_called_once()
        call_args = api_hub.cache.set.call_args
        assert call_args[0][0] == "capabilities"
        caps = call_args[0][1]
        assert caps["climate_sensors"]["status"] == "promoted"
        assert caps["climate_sensors"]["promoted_at"] is not None

    def test_promote_unknown_capability_404(self, api_hub, api_client):
        """Returns 404 for unknown capability name."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "climate_sensors": {"status": "candidate"},
            }
        })

        response = api_client.put("/api/capabilities/nonexistent_cap/promote")
        assert response.status_code == 404
        assert "Unknown capability" in response.json()["detail"]

    def test_promote_no_capabilities_404(self, api_hub, api_client):
        """Returns 404 when capabilities not yet discovered."""
        api_hub.cache.get = AsyncMock(return_value=None)

        response = api_client.put("/api/capabilities/anything/promote")
        assert response.status_code == 404
        assert "Capabilities not found" in response.json()["detail"]


# ============================================================================
# PUT /api/capabilities/{name}/archive
# ============================================================================


class TestArchiveCapability:
    def test_archives_capability(self, api_hub, api_client):
        """Archives a capability and returns 200."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "climate_sensors": {"status": "candidate", "source": "organic"},
            }
        })
        api_hub.cache.set = AsyncMock()

        response = api_client.put("/api/capabilities/climate_sensors/archive")
        assert response.status_code == 200

        data = response.json()
        assert data["capability"] == "climate_sensors"
        assert data["status"] == "archived"

        # Verify cache was updated
        api_hub.cache.set.assert_called_once()
        call_args = api_hub.cache.set.call_args
        caps = call_args[0][1]
        assert caps["climate_sensors"]["status"] == "archived"

    def test_archive_unknown_capability_404(self, api_hub, api_client):
        """Returns 404 for unknown capability name."""
        api_hub.cache.get = AsyncMock(return_value={
            "data": {
                "climate_sensors": {"status": "candidate"},
            }
        })

        response = api_client.put("/api/capabilities/nonexistent_cap/archive")
        assert response.status_code == 404

    def test_archive_no_capabilities_404(self, api_hub, api_client):
        """Returns 404 when capabilities not yet discovered."""
        api_hub.cache.get = AsyncMock(return_value=None)

        response = api_client.put("/api/capabilities/anything/archive")
        assert response.status_code == 404


# ============================================================================
# GET /api/settings/discovery
# ============================================================================


class TestGetDiscoverySettings:
    def test_returns_settings(self, api_hub, api_client, mock_discovery_module):
        """Returns current discovery settings."""
        api_hub.modules["organic_discovery"] = mock_discovery_module

        response = api_client.get("/api/settings/discovery")
        assert response.status_code == 200

        data = response.json()
        assert data["autonomy_mode"] == "suggest_and_wait"
        assert data["promote_threshold"] == 50

    def test_returns_error_when_module_not_loaded(self, api_hub, api_client):
        """Returns error dict when organic discovery module not loaded."""
        response = api_client.get("/api/settings/discovery")
        assert response.status_code == 200

        data = response.json()
        assert "error" in data


# ============================================================================
# PUT /api/settings/discovery
# ============================================================================


class TestUpdateDiscoverySettings:
    def test_updates_settings(self, api_hub, api_client, mock_discovery_module):
        """Updates discovery settings and returns 200."""
        api_hub.modules["organic_discovery"] = mock_discovery_module

        response = api_client.put(
            "/api/settings/discovery",
            json={"autonomy_mode": "auto_promote", "promote_threshold": 40},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "updated"
        mock_discovery_module.update_settings.assert_called_once_with(
            {"autonomy_mode": "auto_promote", "promote_threshold": 40}
        )

    def test_update_module_not_loaded_404(self, api_hub, api_client):
        """Returns 404 when organic discovery module not loaded."""
        response = api_client.put(
            "/api/settings/discovery",
            json={"autonomy_mode": "auto_promote"},
        )
        assert response.status_code == 404


# ============================================================================
# POST /api/discovery/run
# ============================================================================


class TestTriggerDiscoveryRun:
    def test_triggers_run(self, api_hub, api_client, mock_discovery_module):
        """Triggers discovery run and returns started."""
        api_hub.modules["organic_discovery"] = mock_discovery_module

        response = api_client.post("/api/discovery/run")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"

    def test_run_module_not_loaded_404(self, api_hub, api_client):
        """Returns 404 when organic discovery module not loaded."""
        response = api_client.post("/api/discovery/run")
        assert response.status_code == 404


# ============================================================================
# GET /api/discovery/status
# ============================================================================


class TestGetDiscoveryStatus:
    def test_returns_status_with_history(self, api_hub, api_client, mock_discovery_module):
        """Returns discovery status with last run info."""
        mock_discovery_module.history = [
            {"timestamp": "2026-02-13", "clusters_found": 4},
            {"timestamp": "2026-02-14", "clusters_found": 5},
        ]
        api_hub.modules["organic_discovery"] = mock_discovery_module

        response = api_client.get("/api/discovery/status")
        assert response.status_code == 200

        data = response.json()
        assert data["loaded"] is True
        assert data["last_run"] == "2026-02-14"
        assert data["total_runs"] == 2
        assert data["settings"]["autonomy_mode"] == "suggest_and_wait"

    def test_returns_status_no_history(self, api_hub, api_client, mock_discovery_module):
        """Returns status with null last_run when no history."""
        api_hub.modules["organic_discovery"] = mock_discovery_module

        response = api_client.get("/api/discovery/status")
        assert response.status_code == 200

        data = response.json()
        assert data["loaded"] is True
        assert data["last_run"] is None
        assert data["total_runs"] == 0

    def test_returns_not_loaded_when_no_module(self, api_hub, api_client):
        """Returns loaded=False when module not registered."""
        response = api_client.get("/api/discovery/status")
        assert response.status_code == 200

        data = response.json()
        assert data["loaded"] is False
