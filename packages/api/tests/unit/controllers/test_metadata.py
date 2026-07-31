from api.controllers.metadata import list_component_types
from core.domain.entities.config_snapshot import (
    CONFIGURABLE_COMPONENT_TYPES,
    EXPORTABLE_COMPONENT_TYPES,
    NETWORK_TYPES,
)
from litestar.testing import create_test_client


def _get():
    with create_test_client(route_handlers=[list_component_types]) as client:
        return client.get("/component-types")


class TestMetadataController:
    def test_it_returns_all_three_vocabularies(self):
        response = _get()

        assert response.status_code == 200
        data = response.json()
        assert set(data) == {"exportable", "configurable", "network"}

    def test_it_serves_the_sets_core_validates_against(self):
        data = _get().json()

        assert set(data["exportable"]) == EXPORTABLE_COMPONENT_TYPES
        assert set(data["configurable"]) == CONFIGURABLE_COMPONENT_TYPES
        assert set(data["network"]) == NETWORK_TYPES

    def test_it_offers_the_types_the_web_selector_used_to_omit(self):
        data = _get().json()

        for component_type in ("light", "em", "eth", "rgbw", "bthome"):
            assert component_type in data["configurable"]
        assert "schedules" in data["exportable"]

    def test_it_sorts_every_list_so_the_selector_order_is_stable(self):
        data = _get().json()

        for key, types in data.items():
            assert types == sorted(types), key

    def test_it_is_mounted_on_the_app(self, app):
        assert any(
            route.path == "/api/metadata/component-types" for route in app.routes
        )
