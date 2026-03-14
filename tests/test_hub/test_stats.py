"""Tests for IpHub install stats reporting."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ipman.hub.stats import report_install, StatsError


class TestReportInstall:
    """Test install stats reporting via counter issue."""

    @patch("ipman.hub.stats.subprocess.run")
    def test_report_success(self, mock_run: MagicMock) -> None:
        """Should comment on the counter issue and add reaction."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        report_install("web-scraper", counter_issue=42)
        assert mock_run.call_count == 2  # comment + reaction

    @patch("ipman.hub.stats.subprocess.run")
    def test_report_comment_content(self, mock_run: MagicMock) -> None:
        """Comment body should contain the skill name."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        report_install("web-scraper", counter_issue=42)
        # First call is the comment
        comment_call = mock_run.call_args_list[0]
        args = comment_call[0][0]
        assert any("web-scraper" in str(a) for a in args)

    @patch("ipman.hub.stats.subprocess.run")
    def test_report_failure_is_non_fatal(self, mock_run: MagicMock) -> None:
        """Stats failure should raise StatsError but not crash the process."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="rate limited",
        )
        with pytest.raises(StatsError):
            report_install("web-scraper", counter_issue=42)

    @patch("ipman.hub.stats.subprocess.run")
    def test_report_with_username(self, mock_run: MagicMock) -> None:
        """Username should be included in the comment."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="",
        )
        report_install("web-scraper", counter_issue=42, username="alice")
        comment_call = mock_run.call_args_list[0]
        args = comment_call[0][0]
        assert any("alice" in str(a) for a in args)
