"""Configuration path resolution helpers (kept small and focused)."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["resolve_config_path"]


def resolve_config_path(
    explicit_path: str | None,
    *,
    start: Path | None = None,
    env_var: str = "SHELLY_CONFIG_FILE",
    filename: str = "config.json",
) -> str | None:
    """Resolve configuration file path.

    Order of resolution:
      1. explicit path (if exists)
      2. walk upward from start (or cwd)
      3. environment variable (if exists)
      4. None
    """
    if explicit_path and Path(explicit_path).exists():
        return explicit_path

    base = start or Path.cwd()
    for candidate in [base, *base.parents]:
        cfg = candidate / filename
        if cfg.exists():
            return str(cfg)

    env_value = os.getenv(env_var)
    if env_value and Path(env_value).exists():
        return env_value
    return None
