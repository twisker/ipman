"""Lightweight i18n — LANG-based Chinese/English auto-switch."""

from __future__ import annotations

import os

_locale: str = "en"

# ---------------------------------------------------------------------------
# Message catalog
# ---------------------------------------------------------------------------

_MESSAGES: dict[str, dict[str, str]] = {
    "install.success": {
        "en": "Installation complete.",
        "zh": "安装完成。",
    },
    "install.installed": {
        "en": "Installed '{name}'.",
        "zh": "已安装 '{name}'。",
    },
    "install.failed": {
        "en": "Install failed: {msg}",
        "zh": "安装失败：{msg}",
    },
    "install.blocked": {
        "en": "BLOCKED: '{name}' — risk {risk}",
        "zh": "已阻止：'{name}' — 风险等级 {risk}",
    },
    "install.warned": {
        "en": "WARNING: '{name}' — risk {risk}",
        "zh": "警告：'{name}' — 风险等级 {risk}",
    },
    "uninstall.success": {
        "en": "Uninstalled '{name}'.",
        "zh": "已卸载 '{name}'。",
    },
    "pack.success": {
        "en": "Packed {count} skill(s) into {path}",
        "zh": "已将 {count} 个技能打包到 {path}",
    },
    "hub.search.no_results": {
        "en": "No results found.",
        "zh": "未找到结果。",
    },
    "hub.publish.blocked": {
        "en": "Publish blocked: HIGH/EXTREME risk.",
        "zh": "发布被阻止：风险等级为 HIGH/EXTREME。",
    },
    "hub.report.success": {
        "en": "Reported '{name}'. Thank you for helping keep IpHub safe.",
        "zh": "已举报 '{name}'。感谢您帮助维护 IpHub 安全。",
    },
    "env.created": {
        "en": "Created environment '{name}'.",
        "zh": "已创建环境 '{name}'。",
    },
    "env.activated": {
        "en": "Activated environment '{name}'.",
        "zh": "已激活环境 '{name}'。",
    },
    "env.deactivated": {
        "en": "Deactivated environment.",
        "zh": "已停用环境。",
    },
    "error.no_agent": {
        "en": "No agent detected. Use --agent to specify one.",
        "zh": "未检测到 Agent 工具。请使用 --agent 指定。",
    },
    "error.not_found": {
        "en": "'{name}' not found.",
        "zh": "未找到 '{name}'。",
    },
    "security.log_entry": {
        "en": "{action} {name} source={source} risk={risk}",
        "zh": "{action} {name} 来源={source} 风险={risk}",
    },
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def detect_locale() -> str:
    """Detect locale from environment variables."""
    for var in ("LC_ALL", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val.startswith("zh"):
            return "zh"
    return "en"


def set_locale(locale: str) -> None:
    """Manually set the active locale."""
    global _locale
    _locale = locale


def get_locale() -> str:
    """Get the current active locale."""
    return _locale


def t(key: str, **kwargs: str | int) -> str:
    """Translate a message key with optional format args."""
    messages = _MESSAGES.get(key)
    if messages is None:
        return key
    template = messages.get(_locale, messages.get("en", key))
    if kwargs:
        return template.format(**kwargs)
    return template
