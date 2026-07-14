from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _str(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass
class Settings:
    twitch_client_id: str = field(default_factory=lambda: _str("TWITCH_CLIENT_ID", ""))
    twitch_client_secret: str = field(default_factory=lambda: _str("TWITCH_CLIENT_SECRET", ""))
    twitch_redirect_uri: str = field(default_factory=lambda: _str(
        "TWITCH_REDIRECT_URI",
        "http://localhost:17563/callback",
    ))
    twitch_channel: str = field(default_factory=lambda: _str("TWITCH_CHANNEL", "dad_r3x"))

    obs_host: str = field(default_factory=lambda: _str("OBS_HOST", "127.0.0.1"))
    obs_port: int = field(default_factory=lambda: _int("OBS_PORT", 4455))
    obs_password: str = field(default_factory=lambda: _str("OBS_PASSWORD", ""))

    ai_provider: str = field(default_factory=lambda: _str("AI_PROVIDER", "off").lower())
    openai_api_key: str = field(default_factory=lambda: _str("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: _str("OPENAI_MODEL", "gpt-4.1-mini"))

    obs_poll_seconds: int = field(default_factory=lambda: _int("OBS_POLL_SECONDS", 3))
    twitch_analytics_seconds: int = field(default_factory=lambda: _int("TWITCH_ANALYTICS_SECONDS", 60))
    ai_refresh_seconds: int = field(default_factory=lambda: _int("AI_REFRESH_SECONDS", 45))
    report_to_discord: bool = field(default_factory=lambda: _bool("REPORT_TO_DISCORD", False))
