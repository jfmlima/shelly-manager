"""Tests for CLI-specific container lifecycle and compatibility."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from cli.dependencies import container as container_module
from cli.dependencies.container import CLIContainer
from core.repositories.models import Base


@pytest.mark.asyncio
async def test_it_initializes_the_database_schema(monkeypatch):
    connection = MagicMock()
    connection.run_sync = AsyncMock()
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock(return_value=connection)
    transaction.__aexit__ = AsyncMock()
    engine = MagicMock()
    engine.begin.return_value = transaction
    monkeypatch.setattr(container_module, "engine", engine)

    await CLIContainer().initialize_database()

    connection.run_sync.assert_awaited_once_with(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_it_disposes_the_database_engine_on_close(monkeypatch):
    engine = MagicMock()
    engine.dispose = AsyncMock()
    monkeypatch.setattr(container_module, "engine", engine)

    await CLIContainer().close()

    engine.dispose.assert_awaited_once()


def test_it_preserves_the_legacy_scan_interactor_name():
    container = CLIContainer()
    expected = object()
    container.get_scan_interactor = Mock(return_value=expected)

    assert container.get_device_scan_interactor() is expected
