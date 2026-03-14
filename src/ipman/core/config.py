"""Configuration file loading and merging."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_HUB_URL = (
    "https://raw.githubusercontent.com/twisker/iphub/main"
)


class SecurityMode(Enum):
    """Security enforcement level."""

    PERMISSIVE = "permissive"
    DEFAULT = "default"
    CAUTIOUS = "cautious"
    STRICT = "strict"


@dataclass(frozen=True)
class IpManConfig:
    """Immutable configuration object."""

    security_mode: SecurityMode = SecurityMode.DEFAULT
    log_enabled: bool = True
    log_path: Path = field(
        default_factory=lambda: Path.home() / ".ipman" / "security.log",
    )
    hub_url: str = _DEFAULT_HUB_URL
    agent_default: str = "auto"


def load_config(
    *,
    config_dir: Path | None = None,
) -> IpManConfig:
    """Load configuration with priority: env vars > file > defaults.

    Args:
        config_dir: Directory containing config.yaml.
                    Defaults to ``~/.ipman``.
    """
    if config_dir is None:
        config_dir = Path.home() / ".ipman"

    # --- Load file ---
    data: dict[str, Any] = {}
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        raw = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data = raw

    security = data.get("security", {}) or {}
    hub = data.get("hub", {}) or {}
    agent = data.get("agent", {}) or {}

    # --- Security mode ---
    mode_str = security.get("mode", "default")
    try:
        mode = SecurityMode(mode_str)
    except ValueError:
        mode = SecurityMode.DEFAULT

    # --- Log ---
    log_enabled = security.get("log_enabled", True)
    log_path_str = security.get("log_path")
    log_path = Path(log_path_str) if log_path_str else config_dir / "security.log"

    # --- Hub ---
    hub_url = hub.get("url", _DEFAULT_HUB_URL)

    # --- Agent ---
    agent_default = agent.get("default", "auto")

    # --- Environment variable overrides ---
    env_hub = os.environ.get("IPMAN_HUB_URL")
    if env_hub:
        hub_url = env_hub

    env_mode = os.environ.get("IPMAN_SECURITY_MODE")
    if env_mode:
        with contextlib.suppress(ValueError):
            mode = SecurityMode(env_mode)

    return IpManConfig(
        security_mode=mode,
        log_enabled=log_enabled,
        log_path=log_path,
        hub_url=hub_url,
        agent_default=agent_default,
    )
