from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    twitch_client_id: str = os.getenv("TWITCH_CLIENT_ID", "")
    twitch_client_secret: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    twitch_redirect_uri: str = os.getenv(
        "TWITCH_REDIRECT_URI",
        "http://localhost:17563/callback",
    )
    twitch_channel: str = os.getenv("TWITCH_CHANNEL", "dad_r3x")

    obs_host: str = os.getenv("OBS_HOST", "127.0.0.1")
    obs_port: int = _int("OBS_PORT", 4455)
    obs_password: str = os.getenv("OBS_PASSWORD", "")

    ai_provider: str = os.getenv("AI_PROVIDER", "off").lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    obs_poll_seconds: int = _int("OBS_POLL_SECONDS", 3)
    twitch_analytics_seconds: int = _int("TWITCH_ANALYTICS_SECONDS", 60)
    ai_refresh_seconds: int = _int("AI_REFRESH_SECONDS", 45)
