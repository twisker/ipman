"""Skill risk assessment engine — red flag detection + risk classification."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum


class RiskLevel(IntEnum):
    """Risk severity levels (ordered for comparison)."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    EXTREME = 3


@dataclass
class RiskFlag:
    """A single detected risk indicator."""

    id: str
    description: str
    severity: RiskLevel


@dataclass
class VetReport:
    """Complete risk assessment report."""

    skill_name: str
    risk_level: RiskLevel
    verdict: str
    flags: list[RiskFlag] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Content scanning patterns
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str], RiskLevel]] = [
    # Network exfiltration
    (
        "network-exfil",
        re.compile(r"\b(curl|wget)\b", re.IGNORECASE),
        RiskLevel.HIGH,
    ),
    # Raw IP address in URLs
    (
        "raw-ip",
        re.compile(
            r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        ),
        RiskLevel.HIGH,
    ),
    # Credential / sensitive path access
    (
        "credential-access",
        re.compile(
            r"~/?\.(ssh|aws|config|gnupg|kube)/",
            re.IGNORECASE,
        ),
        RiskLevel.HIGH,
    ),
    # Obfuscated code (base64 decode)
    (
        "obfuscated-code",
        re.compile(
            r"\bbase64\b.*\b(decode|--decode|-d)\b",
            re.IGNORECASE,
        ),
        RiskLevel.HIGH,
    ),
    # Dynamic code evaluation
    (
        "obfuscated-code",
        re.compile(r"\beval\s*\(", re.IGNORECASE),
        RiskLevel.HIGH,
    ),
    # Privilege escalation
    (
        "privilege-escalation",
        re.compile(r"\bsudo\b", re.IGNORECASE),
        RiskLevel.HIGH,
    ),
    # Agent memory file access
    (
        "memory-access",
        re.compile(
            r"\b(MEMORY\.md|SOUL\.md|IDENTITY\.md|USER\.md)\b",
        ),
        RiskLevel.EXTREME,
    ),
]


def vet_skill_content(content: str) -> list[RiskFlag]:
    """Scan skill content for red flags.

    Analyzes text (SKILL.md, code files, etc.) for suspicious
    patterns that indicate potential security threats.
    """
    flags: list[RiskFlag] = []
    seen_ids: set[str] = set()

    for flag_id, pattern, severity in _PATTERNS:
        match = pattern.search(content)
        if match and flag_id not in seen_ids:
            seen_ids.add(flag_id)
            flags.append(RiskFlag(
                id=flag_id,
                description=f"Detected: {match.group(0)}",
                severity=severity,
            ))

    return flags


# ---------------------------------------------------------------------------
# Metadata-based checks
# ---------------------------------------------------------------------------

_REPORTS_THRESHOLD = 3
_LOW_INSTALLS_THRESHOLD = 10


def vet_skill_metadata(
    *,
    author: str,
    installs: int,
    reports: int,
) -> list[RiskFlag]:
    """Check metadata-based risk signals."""
    flags: list[RiskFlag] = []

    if reports >= _REPORTS_THRESHOLD:
        flags.append(RiskFlag(
            id="high-reports",
            description=f"{reports} community reports",
            severity=RiskLevel.HIGH,
        ))

    if installs < _LOW_INSTALLS_THRESHOLD:
        flags.append(RiskFlag(
            id="low-reputation",
            description=(
                f"Low install count ({installs}) "
                f"by {author}"
            ),
            severity=RiskLevel.MEDIUM,
        ))

    return flags


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------

_VERDICTS = {
    RiskLevel.LOW: "SAFE TO INSTALL",
    RiskLevel.MEDIUM: "INSTALL WITH CAUTION",
    RiskLevel.HIGH: "DO NOT INSTALL",
    RiskLevel.EXTREME: "DO NOT INSTALL",
}


def assess_risk(
    flags: list[RiskFlag],
    *,
    skill_name: str,
) -> VetReport:
    """Compute overall risk level from collected flags."""
    if not flags:
        return VetReport(
            skill_name=skill_name,
            risk_level=RiskLevel.LOW,
            verdict=_VERDICTS[RiskLevel.LOW],
            flags=[],
        )

    highest = max(f.severity for f in flags)
    return VetReport(
        skill_name=skill_name,
        risk_level=RiskLevel(highest),
        verdict=_VERDICTS[RiskLevel(highest)],
        flags=flags,
    )
