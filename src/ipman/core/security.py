"""Security enforcement — decision matrix and logging."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from ipman.core.config import SecurityMode
from ipman.core.vetter import RiskLevel


class Action(Enum):
    """Install-time action determined by risk level x security mode."""

    INSTALL = "INSTALL"
    WARN_INSTALL = "WARN_INSTALL"
    WARN_CONFIRM = "WARN_CONFIRM"
    BLOCK = "BLOCK"


# Decision matrix: _MATRIX[security_mode][risk_level] -> Action
_MATRIX: dict[SecurityMode, dict[RiskLevel, Action]] = {
    SecurityMode.PERMISSIVE: {
        RiskLevel.LOW: Action.INSTALL,
        RiskLevel.MEDIUM: Action.INSTALL,
        RiskLevel.HIGH: Action.INSTALL,
        RiskLevel.EXTREME: Action.WARN_INSTALL,
    },
    SecurityMode.DEFAULT: {
        RiskLevel.LOW: Action.INSTALL,
        RiskLevel.MEDIUM: Action.INSTALL,
        RiskLevel.HIGH: Action.WARN_INSTALL,
        RiskLevel.EXTREME: Action.BLOCK,
    },
    SecurityMode.CAUTIOUS: {
        RiskLevel.LOW: Action.INSTALL,
        RiskLevel.MEDIUM: Action.WARN_INSTALL,
        RiskLevel.HIGH: Action.BLOCK,
        RiskLevel.EXTREME: Action.BLOCK,
    },
    SecurityMode.STRICT: {
        RiskLevel.LOW: Action.INSTALL,
        RiskLevel.MEDIUM: Action.WARN_CONFIRM,
        RiskLevel.HIGH: Action.BLOCK,
        RiskLevel.EXTREME: Action.BLOCK,
    },
}


def decide_action(
    risk_level: RiskLevel,
    security_mode: SecurityMode,
) -> Action:
    """Determine the install action for a given risk + mode."""
    return _MATRIX[security_mode][risk_level]


def log_security_event(
    *,
    log_path: Path,
    skill_name: str,
    source: str,
    risk_level: RiskLevel,
    action: Action,
    details: str = "",
) -> None:
    """Append a security event to the log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [
        ts,
        action.value,
        skill_name,
        f"source={source}",
        f"risk={risk_level.name}",
    ]
    if details:
        parts.append(f"reason={details}")

    line = " ".join(parts)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
