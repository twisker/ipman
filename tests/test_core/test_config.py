"""Tests for configuration file loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ipman.core.config import IpManConfig, SecurityMode, load_config


class TestSecurityMode:
    """Test SecurityMode enum."""

    def test_all_modes_exist(self) -> None:
        assert SecurityMode.PERMISSIVE.value == "permissive"
        assert SecurityMode.DEFAULT.value == "default"
        assert SecurityMode.CAUTIOUS.value == "cautious"
        assert SecurityMode.STRICT.value == "strict"

    def test_from_string(self) -> None:
        assert SecurityMode("permissive") == SecurityMode.PERMISSIVE
        assert SecurityMode("strict") == SecurityMode.STRICT

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValueError):
            SecurityMode("invalid")


class TestLoadConfig:
    """Test load_config()."""

    def test_defaults_when_no_file(self, tmp_path: Path) -> None:
        """No config file should return all defaults."""
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.DEFAULT
        assert cfg.log_enabled is True
        assert cfg.log_path == tmp_path / "security.log"
        assert cfg.hub_url == "https://raw.githubusercontent.com/twisker/iphub/main"
        assert cfg.agent_default == "auto"

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Config file values should override defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "security": {
                "mode": "strict",
                "log_enabled": False,
            },
            "hub": {
                "url": "https://mirror.example.com/iphub/main",
            },
            "agent": {
                "default": "claude-code",
            },
        }))
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.STRICT
        assert cfg.log_enabled is False
        assert cfg.hub_url == "https://mirror.example.com/iphub/main"
        assert cfg.agent_default == "claude-code"

    def test_partial_config(self, tmp_path: Path) -> None:
        """Partial config should only override specified fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "security": {"mode": "cautious"},
        }))
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.CAUTIOUS
        # Other fields remain default
        assert cfg.log_enabled is True
        assert cfg.agent_default == "auto"

    def test_empty_config_file(self, tmp_path: Path) -> None:
        """Empty config file should return defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.DEFAULT

    def test_custom_log_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "security": {"log_path": "/var/log/ipman.log"},
        }))
        cfg = load_config(config_dir=tmp_path)
        assert cfg.log_path == Path("/var/log/ipman.log")

    def test_env_override_hub_url(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variable should override config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "hub": {"url": "https://from-config.example.com"},
        }))
        monkeypatch.setenv("IPMAN_HUB_URL", "https://from-env.example.com")
        cfg = load_config(config_dir=tmp_path)
        assert cfg.hub_url == "https://from-env.example.com"

    def test_env_override_security_mode(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("IPMAN_SECURITY_MODE", "strict")
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.STRICT

    def test_invalid_mode_in_file(self, tmp_path: Path) -> None:
        """Invalid mode in config should fall back to default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "security": {"mode": "invalid_mode"},
        }))
        cfg = load_config(config_dir=tmp_path)
        assert cfg.security_mode == SecurityMode.DEFAULT


class TestIpManConfig:
    """Test IpManConfig dataclass."""

    def test_is_frozen(self) -> None:
        """Config should be immutable."""
        cfg = IpManConfig()
        with pytest.raises(AttributeError):
            cfg.security_mode = SecurityMode.STRICT  # type: ignore[misc]
