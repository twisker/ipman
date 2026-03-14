"""IpHub publisher — fork, create registry files, submit PR via gh CLI."""

from __future__ import annotations

import base64
import subprocess
from datetime import date
from typing import Any

import yaml

from ipman.core.package import IPPackage

_IPHUB_REPO = "twisker/iphub"


def _dump_yaml(data: dict[str, Any]) -> str:
    """Dump dict to YAML string with standard formatting."""
    return yaml.dump(
        data, default_flow_style=False,
        allow_unicode=True, sort_keys=False,
    )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PublishError(Exception):
    """Raised when a publish operation fails."""


# ---------------------------------------------------------------------------
# GitHub identity
# ---------------------------------------------------------------------------

def get_github_username() -> str:
    """Get the authenticated GitHub username via ``gh auth status``."""
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise PublishError(
            "GitHub authentication required. Run `gh auth login` first."
        )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Registry file generation
# ---------------------------------------------------------------------------

def generate_skill_registry(
    *,
    name: str,
    description: str,
    author: str,
    license_: str | None = None,
    homepage: str | None = None,
    keywords: list[str] | None = None,
    agents: dict[str, dict[str, str]] | None = None,
    risk_level: str | None = None,
) -> dict[str, Any]:
    """Generate a skill registry dict (for registry/@owner/<name>.yaml)."""
    data: dict[str, Any] = {
        "type": "skill",
        "name": name,
        "description": description,
        "author": author,
    }
    if license_:
        data["license"] = license_
    if homepage:
        data["homepage"] = homepage
    if keywords:
        data["keywords"] = keywords
    if agents:
        data["agents"] = agents
    if risk_level:
        data["risk_level"] = risk_level
    return data


def generate_package_registry(
    *,
    name: str,
    description: str,
    author: str,
    license_: str | None = None,
    homepage: str | None = None,
    risk_level: str | None = None,
) -> dict[str, Any]:
    """Generate a package meta.yaml dict."""
    data: dict[str, Any] = {
        "type": "ip",
        "name": name,
        "description": description,
        "author": author,
    }
    if license_:
        data["license"] = license_
    if homepage:
        data["homepage"] = homepage
    if risk_level:
        data["risk_level"] = risk_level
    return data


def generate_version_data(pkg: IPPackage) -> dict[str, Any]:
    """Generate a package version file dict from an IPPackage."""
    data: dict[str, Any] = {
        "version": pkg.version,
        "released": str(date.today()),
        "skills": [{"name": s.name} for s in pkg.skills],
    }
    if pkg.dependencies:
        deps = []
        for d in pkg.dependencies:
            entry: dict[str, Any] = {"name": d.name}
            if d.version:
                entry["version"] = d.version
            if d.source:
                entry["source"] = d.source
            deps.append(entry)
        data["dependencies"] = deps
    return data


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

class IpHubPublisher:
    """Orchestrates the publish workflow via gh CLI.

    Steps:
      1. ensure_fork() — fork iphub repo if not already forked
      2. Create a branch on the fork
      3. Push registry file(s) to the branch
      4. Create a PR from fork branch to upstream main
    """

    def __init__(self, username: str) -> None:
        self.username = username
        self._is_owner = self._check_owner(username)
        self.target_repo = (
            _IPHUB_REPO if self._is_owner
            else f"{username}/iphub"
        )

    @staticmethod
    def _check_owner(username: str) -> bool:
        """Check if the user is the iphub repo owner."""
        owner = _IPHUB_REPO.split("/")[0]
        return username.lower() == owner.lower()

    def _gh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Run a gh CLI command."""
        result = subprocess.run(
            ["gh", *args],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "gh command failed"
            raise PublishError(f"gh error: {msg}")
        return result

    def ensure_fork(self) -> None:
        """Fork the iphub repo if not already forked.

        Skipped for the repo owner (can't fork own repo).
        """
        if self._is_owner:
            return
        self._gh(["repo", "fork", _IPHUB_REPO, "--clone=false"])

    def _push_file(
        self, branch: str, path: str, content: str, message: str,
    ) -> None:
        """Create or update a file on a branch via GitHub API."""
        encoded = base64.b64encode(content.encode()).decode()
        self._gh([
            "api", "-X", "PUT",
            f"repos/{self.target_repo}/contents/{path}",
            "-f", f"message={message}",
            "-f", f"content={encoded}",
            "-f", f"branch={branch}",
        ])

    def _create_branch(self, branch: str) -> None:
        """Create a branch on the fork from upstream main."""
        # Get upstream main SHA
        result = self._gh([
            "api", f"repos/{_IPHUB_REPO}/git/ref/heads/main",
            "--jq", ".object.sha",
        ])
        sha = result.stdout.strip()
        # Create branch
        self._gh([
            "api", "-X", "POST",
            f"repos/{self.target_repo}/git/refs",
            "-f", f"ref=refs/heads/{branch}",
            "-f", f"sha={sha}",
        ])

    def _create_pr(self, branch: str, title: str, body: str) -> str:
        """Create a PR to upstream main."""
        # Owner: PR within same repo (head=branch)
        # Contributor: PR from fork (head=user:branch)
        head = branch if self._is_owner else f"{self.username}:{branch}"
        result = self._gh([
            "pr", "create",
            "--repo", _IPHUB_REPO,
            "--head", head,
            "--base", "main",
            "--title", title,
            "--body", body,
        ])
        return result.stdout.strip()

    def publish_skill(
        self,
        name: str,
        description: str,
        agents: dict[str, dict[str, str]] | None = None,
        license_: str | None = None,
        homepage: str | None = None,
        keywords: list[str] | None = None,
        risk_level: str = "LOW",
        vet_summary: str = "",
    ) -> str:
        """Publish a skill to IpHub. Returns PR URL."""
        self.ensure_fork()

        registry = generate_skill_registry(
            name=name,
            description=description,
            author=f"@{self.username}",
            license_=license_,
            homepage=homepage,
            keywords=keywords,
            agents=agents,
            risk_level=risk_level,
        )
        content = _dump_yaml(registry)

        branch = f"publish/{name}"
        self._create_branch(branch)

        path = f"registry/@{self.username}/{name}.yaml"
        self._push_file(
            branch, path, content, f"Register skill: {name}",
        )

        pr_body = (
            f"Register `{name}` skill by @{self.username}.\n\n"
            f"## Risk Assessment\n\n"
            f"**Risk Level:** {risk_level}\n\n"
        )
        if vet_summary:
            pr_body += f"**Details:**\n{vet_summary}\n"

        return self._create_pr(
            branch,
            f"Register skill: {name}",
            pr_body,
        )

    def publish_package(
        self,
        pkg: IPPackage,
        risk_level: str = "LOW",
        vet_summary: str = "",
    ) -> str:
        """Publish an IP package to IpHub. Returns PR URL."""
        self.ensure_fork()

        branch = f"publish/{pkg.name}-v{pkg.version}"
        self._create_branch(branch)

        # meta.yaml
        meta = generate_package_registry(
            name=pkg.name,
            description=pkg.description,
            author=f"@{self.username}",
            license_=pkg.license,
            risk_level=risk_level,
        )
        meta_content = _dump_yaml(meta)
        meta_path = (
            f"registry/@{self.username}/{pkg.name}/meta.yaml"
        )
        self._push_file(
            branch, meta_path, meta_content,
            f"Register package: {pkg.name}",
        )

        # version file
        version_data = generate_version_data(pkg)
        version_content = _dump_yaml(version_data)
        version_path = (
            f"registry/@{self.username}"
            f"/{pkg.name}/{pkg.version}.yaml"
        )
        self._push_file(
            branch, version_path, version_content,
            f"Add {pkg.name} v{pkg.version}",
        )

        pr_body = (
            f"Register `{pkg.name}` v{pkg.version}"
            f" by @{self.username}.\n\n"
            f"## Risk Assessment\n\n"
            f"**Risk Level:** {risk_level}\n\n"
        )
        if vet_summary:
            pr_body += f"**Details:**\n{vet_summary}\n"

        return self._create_pr(
            branch,
            f"Register package: {pkg.name} v{pkg.version}",
            pr_body,
        )
