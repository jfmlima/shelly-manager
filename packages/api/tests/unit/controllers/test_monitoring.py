from api.controllers.monitoring import (
    get_action_history,
    health_check,
)
from litestar.testing import create_test_client


class TestMonitoringController:

    def test_it_returns_health_check_successfully(self):
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert data["service"] == "shelly-manager-api"
            assert "timestamp" in data

    def test_it_returns_action_history_placeholder(self):
        with create_test_client(route_handlers=[get_action_history]) as client:
            response = client.get("/actions")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["actions"] == []
            assert data["message"] == "Action history not yet implemented"
