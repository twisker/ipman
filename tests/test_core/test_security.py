"""Tests for security enforcement and logging."""

from __future__ import annotations

from pathlib import Path

import pytest

from ipman.core.config import SecurityMode
from ipman.core.security import (
    Action,
    decide_action,
    log_security_event,
)
from ipman.core.vetter import RiskLevel


# ---------------------------------------------------------------------------
# Decision matrix
# ---------------------------------------------------------------------------

class TestDecideAction:
    """Test the risk level x security mode decision matrix."""

    # --- PERMISSIVE ---
    def test_permissive_low(self) -> None:
        assert decide_action(RiskLevel.LOW, SecurityMode.PERMISSIVE) == Action.INSTALL

    def test_permissive_medium(self) -> None:
        assert decide_action(RiskLevel.MEDIUM, SecurityMode.PERMISSIVE) == Action.INSTALL

    def test_permissive_high(self) -> None:
        assert decide_action(RiskLevel.HIGH, SecurityMode.PERMISSIVE) == Action.INSTALL

    def test_permissive_extreme(self) -> None:
        assert decide_action(RiskLevel.EXTREME, SecurityMode.PERMISSIVE) == Action.WARN_INSTALL

    # --- DEFAULT ---
    def test_default_low(self) -> None:
        assert decide_action(RiskLevel.LOW, SecurityMode.DEFAULT) == Action.INSTALL

    def test_default_medium(self) -> None:
        assert decide_action(RiskLevel.MEDIUM, SecurityMode.DEFAULT) == Action.INSTALL

    def test_default_high(self) -> None:
        assert decide_action(RiskLevel.HIGH, SecurityMode.DEFAULT) == Action.WARN_INSTALL

    def test_default_extreme(self) -> None:
        assert decide_action(RiskLevel.EXTREME, SecurityMode.DEFAULT) == Action.BLOCK

    # --- CAUTIOUS ---
    def test_cautious_low(self) -> None:
        assert decide_action(RiskLevel.LOW, SecurityMode.CAUTIOUS) == Action.INSTALL

    def test_cautious_medium(self) -> None:
        assert decide_action(RiskLevel.MEDIUM, SecurityMode.CAUTIOUS) == Action.WARN_INSTALL

    def test_cautious_high(self) -> None:
        assert decide_action(RiskLevel.HIGH, SecurityMode.CAUTIOUS) == Action.BLOCK

    def test_cautious_extreme(self) -> None:
        assert decide_action(RiskLevel.EXTREME, SecurityMode.CAUTIOUS) == Action.BLOCK

    # --- STRICT ---
    def test_strict_low(self) -> None:
        assert decide_action(RiskLevel.LOW, SecurityMode.STRICT) == Action.INSTALL

    def test_strict_medium(self) -> None:
        assert decide_action(RiskLevel.MEDIUM, SecurityMode.STRICT) == Action.WARN_CONFIRM

    def test_strict_high(self) -> None:
        assert decide_action(RiskLevel.HIGH, SecurityMode.STRICT) == Action.BLOCK

    def test_strict_extreme(self) -> None:
        assert decide_action(RiskLevel.EXTREME, SecurityMode.STRICT) == Action.BLOCK


# ---------------------------------------------------------------------------
# Security logging
# ---------------------------------------------------------------------------

class TestLogSecurityEvent:
    """Test security log file writing."""

    def test_log_writes_entry(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        log_security_event(
            log_path=log_file,
            skill_name="bad-tool",
            source="https://evil.com/bad.ip.yaml",
            risk_level=RiskLevel.EXTREME,
            action=Action.BLOCK,
            details="credential harvesting detected",
        )
        content = log_file.read_text()
        assert "bad-tool" in content
        assert "EXTREME" in content
        assert "BLOCK" in content
        assert "credential harvesting" in content

    def test_log_appends(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        log_security_event(
            log_path=log_file,
            skill_name="first",
            source="iphub",
            risk_level=RiskLevel.HIGH,
            action=Action.WARN_INSTALL,
        )
        log_security_event(
            log_path=log_file,
            skill_name="second",
            source="local",
            risk_level=RiskLevel.EXTREME,
            action=Action.BLOCK,
        )
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_log_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_file = tmp_path / "subdir" / "deep" / "security.log"
        log_security_event(
            log_path=log_file,
            skill_name="test",
            source="local",
            risk_level=RiskLevel.MEDIUM,
            action=Action.WARN_INSTALL,
        )
        assert log_file.exists()
