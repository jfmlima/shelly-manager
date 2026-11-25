"""Tests for the CLI container against a real, empty database."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.dependencies import container as container_module
from cli.dependencies.container import CLIContainer
from cli.exceptions import EXIT_NOT_FOUND
from cli.main import cli
from click.testing import CliRunner
from core.dependencies import container_base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
def fresh_database(tmp_path, monkeypatch):
    """Point every CLI command at an empty database file with no tables."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}")
    monkeypatch.setattr(container_base, "engine", engine)
    monkeypatch.setattr(
        container_base,
        "async_session_factory",
        async_sessionmaker(engine, expire_on_commit=False),
    )
    monkeypatch.setattr(container_module, "engine", engine)
    return engine


@pytest.mark.parametrize("args", [["backup", "list"], ["backup", "schedule", "list"]])
def test_it_reads_from_a_fresh_database_without_setup(fresh_database, args):
    result = CliRunner().invoke(cli, args)

    assert result.exit_code == 0, result.output
    assert "no such table" not in result.output


def test_it_reports_deleting_a_credential_that_does_not_exist(fresh_database):
    result = CliRunner().invoke(cli, ["credentials", "delete", "11:22:33:44:55:66"])

    assert result.exit_code == EXIT_NOT_FOUND, result.output
    assert "Credentials deleted" not in result.output


def test_it_round_trips_a_credential(fresh_database):
    runner = CliRunner()

    assert (
        runner.invoke(cli, ["credentials", "set", "aa:bb:cc:dd:ee:ff", "pw"]).exit_code
        == 0
    )
    listed = runner.invoke(cli, ["credentials", "list"])
    deleted = runner.invoke(cli, ["credentials", "delete", "AA:BB:CC:DD:EE:FF"])

    assert "AABBCCDDEEFF" in listed.output
    assert deleted.exit_code == 0, deleted.output


@pytest.mark.asyncio
async def test_it_disposes_the_database_engine_on_close(monkeypatch):
    engine = MagicMock()
    engine.dispose = AsyncMock()
    monkeypatch.setattr(container_module, "engine", engine)

    await CLIContainer().close()

    engine.dispose.assert_awaited_once()
