"""IpHub install statistics reporting via GitHub counter issues."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

_IPHUB_REPO = "twisker/iphub"


class StatsError(Exception):
    """Raised when stats reporting fails."""


def report_install(
    name: str,
    counter_issue: int,
    *,
    username: str | None = None,
) -> None:
    """Report a successful install to the counter issue.

    Adds a comment (install count) and a reaction (unique user).
    Failures raise StatsError but should be treated as non-fatal
    by callers — install success is independent of stats reporting.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    user_part = f" by @{username}" if username else ""
    body = f"Installed `{name}`{user_part} at {ts}"

    # Add comment
    result = subprocess.run(
        [
            "gh", "issue", "comment", str(counter_issue),
            "--repo", _IPHUB_REPO,
            "--body", body,
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or "Failed to report install stats"
        raise StatsError(msg)

    # Add reaction (thumbs up) for unique user counting
    subprocess.run(
        [
            "gh", "api", "-X", "POST",
            f"repos/{_IPHUB_REPO}/issues/{counter_issue}/reactions",
            "-f", "content=+1",
        ],
        capture_output=True, text=True, check=False,
    )
