"""Performance benchmark tests — validation-registry.md acceptance criteria.

Thresholds (from validation-registry.md + tech-spec-registry.md):
  - CLI cold start:          < 500ms
  - Single skill install:    < 5s (local), < 15s (network)
  - Dependency resolution:   50 deps < 3s

Each test runs multiple iterations and asserts against the *median* to avoid
false failures from transient OS jitter. CI machines are slower than dev
machines, so all thresholds include a safety margin.
"""
from __future__ import annotations

import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.performance

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IPMAN_ROOT = Path(__file__).parent.parent.parent
_PYTHON = sys.executable


def _time_subprocess(cmd: list[str], runs: int = 5) -> float:
    """Return median wall-clock time (seconds) for *cmd* over *runs* runs."""
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run(cmd, capture_output=True, check=False)
        times.append(time.perf_counter() - start)
    return statistics.median(times)


# ---------------------------------------------------------------------------
# 1. CLI cold start
# ---------------------------------------------------------------------------

class TestCLIColdStart:
    """CLI cold start must be < 500ms (validation-registry.md)."""

    THRESHOLD_MS = 500

    def test_version_flag_cold_start(self) -> None:
        """``python -m ipman --version`` completes in < 500ms (median of 5)."""
        median_s = _time_subprocess(
            [_PYTHON, "-m", "ipman", "--version"],
            runs=5,
        )
        median_ms = median_s * 1000
        assert median_ms < self.THRESHOLD_MS, (
            f"CLI cold start too slow: {median_ms:.0f}ms "
            f"(threshold: {self.THRESHOLD_MS}ms)"
        )

    def test_help_flag_cold_start(self) -> None:
        """``python -m ipman --help`` completes in < 500ms (median of 5)."""
        median_s = _time_subprocess(
            [_PYTHON, "-m", "ipman", "--help"],
            runs=5,
        )
        median_ms = median_s * 1000
        assert median_ms < self.THRESHOLD_MS, (
            f"--help cold start too slow: {median_ms:.0f}ms "
            f"(threshold: {self.THRESHOLD_MS}ms)"
        )

    def test_records_timing_for_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Print timing for the compliance report (always passes)."""
        median_s = _time_subprocess(
            [_PYTHON, "-m", "ipman", "--version"],
            runs=5,
        )
        print(f"\n[BENCHMARK] CLI cold start: {median_s * 1000:.1f}ms "
              f"(threshold: {self.THRESHOLD_MS}ms)")
        # Always passes — this test is for evidence only


# ---------------------------------------------------------------------------
# 2. Dependency resolver: 50 deps < 3s
# ---------------------------------------------------------------------------

class TestResolverPerformance:
    """Dependency resolver must handle 50 deps in < 3s (validation-registry.md)."""

    THRESHOLD_S = 3.0
    DEP_COUNT = 50

    def _make_chain_fetcher(self, n: int):  # type: ignore[return]
        """Build a fetch function for a linear chain of n packages."""
        registry: dict[str, dict[str, Any]] = {}
        for i in range(n):
            deps = [{"name": f"pkg{i + 1}"}] if i < n - 1 else []
            registry[f"pkg{i}"] = {
                "version": "1.0.0",
                "skills": [{"name": f"skill-{i}"}],
                "dependencies": deps,
            }

        def fetcher(name: str, version: str | None) -> dict[str, Any]:
            return registry.get(name, {"version": "1.0.0", "skills": [], "dependencies": []})

        return fetcher

    def _make_wide_fetcher(self, n: int):  # type: ignore[return]
        """Build a fetch function for a root with n direct dependencies."""
        registry: dict[str, dict[str, Any]] = {
            "root": {
                "version": "1.0.0",
                "skills": [{"name": "root-skill"}],
                "dependencies": [{"name": f"dep{i}"} for i in range(n)],
            }
        }
        for i in range(n):
            registry[f"dep{i}"] = {
                "version": "1.0.0",
                "skills": [{"name": f"dep-skill-{i}"}],
                "dependencies": [],
            }

        def fetcher(name: str, version: str | None) -> dict[str, Any]:
            return registry.get(name, {"version": "1.0.0", "skills": [], "dependencies": []})

        return fetcher

    def test_linear_chain_50_deps(self) -> None:
        """Linear chain of 50 packages resolves in < 3s (median of 10 runs)."""
        from ipman.core.resolver import resolve_dependencies

        fetcher = self._make_chain_fetcher(self.DEP_COUNT)
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter()
            result = resolve_dependencies("pkg0", None, fetcher)
            times.append(time.perf_counter() - start)

        median_s = statistics.median(times)
        assert len(result) == self.DEP_COUNT, (
            f"Expected {self.DEP_COUNT} skills, got {len(result)}"
        )
        assert median_s < self.THRESHOLD_S, (
            f"Linear chain too slow: {median_s * 1000:.2f}ms "
            f"(threshold: {self.THRESHOLD_S * 1000:.0f}ms)"
        )

    def test_wide_tree_50_deps(self) -> None:
        """Root with 50 direct deps resolves in < 3s (median of 10 runs)."""
        from ipman.core.resolver import resolve_dependencies

        fetcher = self._make_wide_fetcher(self.DEP_COUNT)
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter()
            result = resolve_dependencies("root", None, fetcher)
            times.append(time.perf_counter() - start)

        median_s = statistics.median(times)
        # root skill + 50 dep skills = 51
        assert len(result) == self.DEP_COUNT + 1, (
            f"Expected {self.DEP_COUNT + 1} skills, got {len(result)}"
        )
        assert median_s < self.THRESHOLD_S, (
            f"Wide tree too slow: {median_s * 1000:.2f}ms "
            f"(threshold: {self.THRESHOLD_S * 1000:.0f}ms)"
        )

    def test_records_timing_for_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Print timing for the compliance report (always passes)."""
        from ipman.core.resolver import resolve_dependencies

        fetcher = self._make_chain_fetcher(self.DEP_COUNT)
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter()
            resolve_dependencies("pkg0", None, fetcher)
            times.append(time.perf_counter() - start)

        median_ms = statistics.median(times) * 1000
        print(f"\n[BENCHMARK] Resolver 50-node chain: {median_ms:.3f}ms "
              f"(threshold: {self.THRESHOLD_S * 1000:.0f}ms)")


# ---------------------------------------------------------------------------
# 3. Skill install: < 5s (local), < 15s (network) — measured, not enforced in CI
# ---------------------------------------------------------------------------

class TestSkillInstallPerformance:
    """Skill install timing (local dir path, dry-run to avoid real agent calls)."""

    # Dry-run installs do not hit the agent CLI. We time the ipman dispatch
    # layer only. Full install timing requires a real agent and is measured
    # in E2E tests; we record the dry-run overhead here.
    DRYRUN_THRESHOLD_MS = 1000  # dry-run dispatch must be < 1s

    def test_dry_run_install_is_fast(self, tmp_path: Path) -> None:
        """``ipman install --dry-run`` dispatches in < 1s (no agent call)."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# test-skill\nA perf test skill.\n")

        median_s = _time_subprocess(
            [
                _PYTHON, "-m", "ipman",
                "install", str(skill_dir),
                "--dry-run", "--no-vet",
            ],
            runs=5,
        )
        median_ms = median_s * 1000
        assert median_ms < self.DRYRUN_THRESHOLD_MS, (
            f"Dry-run install too slow: {median_ms:.0f}ms "
            f"(threshold: {self.DRYRUN_THRESHOLD_MS}ms)"
        )

    def test_records_timing_for_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Print dry-run timing for the compliance report (always passes)."""
        skill_dir = tmp_path / "bench-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# bench-skill\nA perf test skill.\n")

        median_s = _time_subprocess(
            [_PYTHON, "-m", "ipman", "install", str(skill_dir), "--dry-run", "--no-vet"],
            runs=3,
        )
        print(
            f"\n[BENCHMARK] ipman install --dry-run: {median_s * 1000:.1f}ms "
            f"(full install threshold: 5000ms local / 15000ms network)"
        )
