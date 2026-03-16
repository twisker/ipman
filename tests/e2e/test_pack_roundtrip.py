"""E2E tests for pack/install roundtrip: pack env -> .ip.yaml -> install."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .helpers.run import EnvInfo, run_ipman

pytestmark = [pytest.mark.e2e, pytest.mark.platform]


class TestPackRoundtrip:
    """Verify pack produces valid .ip.yaml and install can consume it."""

    def test_pack_empty_env(
        self, ipman_env: EnvInfo, project_dir: Path,
    ) -> None:
        """Pack an env with no skills; verify .ip.yaml has correct name/version."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        output_file = project_dir / "packed.ip.yaml"
        run_ipman(
            "pack",
            "--name", ipman_env.name,
            "--version", "0.1.0",
            "--agent", ipman_env.agent,
            "--output", str(output_file),
            cwd=project_dir,
        )

        assert output_file.exists()
        data = yaml.safe_load(output_file.read_text())
        assert data["name"] == ipman_env.name
        assert data["version"] == "0.1.0"

    def test_pack_preserves_metadata(
        self, ipman_env: EnvInfo, project_dir: Path,
    ) -> None:
        """Verify name, version, and description are all preserved in YAML."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        output_file = project_dir / "meta.ip.yaml"
        run_ipman(
            "pack",
            "--name", "test-pkg",
            "--version", "2.3.4",
            "--description", "E2E metadata test",
            "--agent", ipman_env.agent,
            "--output", str(output_file),
            cwd=project_dir,
        )

        assert output_file.exists()
        data = yaml.safe_load(output_file.read_text())
        assert data["name"] == "test-pkg"
        assert data["version"] == "2.3.4"
        assert data["description"] == "E2E metadata test"

    def test_pack_install_roundtrip(
        self, ipman_env: EnvInfo, project_dir: Path,
    ) -> None:
        """Pack env-a, then dry-run install into env-b."""
        run_ipman(
            "env", "activate", ipman_env.name, f"--{ipman_env.scope}",
            cwd=project_dir,
        )

        output_file = project_dir / "roundtrip.ip.yaml"
        run_ipman(
            "pack",
            "--name", "roundtrip-pkg",
            "--version", "1.0.0",
            "--agent", ipman_env.agent,
            "--output", str(output_file),
            cwd=project_dir,
        )

        assert output_file.exists()

        # Dry-run install from the packed file
        result = run_ipman(
            "install", str(output_file),
            "--dry-run", "--no-vet",
            cwd=project_dir, check=False,
        )
        # Dry-run should succeed (exit 0) or at least not crash hard
        assert result.returncode == 0, (
            f"Dry-run install failed: {result.stderr}"
        )
