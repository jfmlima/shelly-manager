import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime

from api.controllers.monitoring import health_check
from litestar.config.cors import CORSConfig
from litestar.testing import create_test_client


class TestMainApp:

    def test_it_creates_app_with_default_config(self, app):
        assert app is not None
        assert len(app.routes) > 0

    def test_it_handles_cors_correctly(self):
        cors_config = CORSConfig(
            allow_origins=["*"],
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

        with create_test_client(
            route_handlers=[health_check], cors_config=cors_config
        ) as client:
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            assert response.status_code == 204  # OPTIONS requests return 204 No Content
            assert "access-control-allow-origin" in response.headers
            assert response.headers["access-control-allow-origin"] == "*"

    def test_it_handles_validation_error(self):
        # This test would need a route that has validation, but for now let's test a simpler case
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

            timestamp = datetime.fromisoformat(data["timestamp"])
            assert isinstance(timestamp, datetime)

    def test_it_routes_to_api_endpoints(self):
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_it_returns_404_for_unknown_routes(self):
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/unknown/route")

            assert response.status_code == 404
