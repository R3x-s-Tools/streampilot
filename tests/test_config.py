from __future__ import annotations

from core.config import Settings
from services.discord_reporter import DiscordReporter


def test_settings_report_to_discord_true(monkeypatch):
    monkeypatch.setenv("REPORT_TO_DISCORD", "true")
    settings = Settings()

    assert settings.report_to_discord is True


def test_settings_report_to_discord_false_by_default(monkeypatch):
    monkeypatch.setenv("REPORT_TO_DISCORD", "false")
    settings = Settings()

    assert settings.report_to_discord is False


def test_discord_reporter_disabled_without_webhook(monkeypatch):
    monkeypatch.delenv("DISCORD_REPORT_WEBHOOK_URL", raising=False)

    reporter = DiscordReporter()

    assert reporter.enabled is False
    assert reporter.send_markdown_report("missing.md", {}) is False
