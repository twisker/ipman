"""Tests for i18n module."""

from __future__ import annotations

import pytest

from ipman.utils.i18n import detect_locale, set_locale, t


class TestDetectLocale:
    """Test locale detection from environment."""

    def test_detect_chinese(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANG", "zh_CN.UTF-8")
        assert detect_locale() == "zh"

    def test_detect_chinese_tw(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANG", "zh_TW.UTF-8")
        assert detect_locale() == "zh"

    def test_detect_english(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        assert detect_locale() == "en"

    def test_detect_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LANGUAGE", raising=False)
        assert detect_locale() == "en"

    def test_lc_all_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        monkeypatch.setenv("LC_ALL", "zh_CN.UTF-8")
        assert detect_locale() == "zh"


class TestTranslation:
    """Test translation function."""

    def test_english_message(self) -> None:
        set_locale("en")
        msg = t("install.success")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_chinese_message(self) -> None:
        set_locale("zh")
        msg = t("install.success")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_en_and_zh_differ(self) -> None:
        set_locale("en")
        en = t("install.success")
        set_locale("zh")
        zh = t("install.success")
        assert en != zh

    def test_unknown_key_returns_key(self) -> None:
        set_locale("en")
        assert t("nonexistent.key") == "nonexistent.key"

    def test_format_args(self) -> None:
        set_locale("en")
        msg = t("install.installed", name="web-scraper")
        assert "web-scraper" in msg
