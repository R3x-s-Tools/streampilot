from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.producer_v2 import AiProducerV2
from analytics.logger import StreamLogger
from core.architecture import EventBus, ServiceRegistry
from core.config import Settings
from reports.generator import ReportGenerator
from services.discord_reporter import DiscordReporter
from services.eventsub_service import EventSubService
from connectors.obs_connector import OBSConnector
from services.twitch_api import TwitchApiService
from services.twitch_auth import TwitchAuthService
from services.twitch_chat import TwitchChatService


@dataclass
class ApplicationServices:
    """Compose the application around explicit service boundaries.

    This keeps the presentation layer thin and makes the system easier to test,
    evolve, and extend while preserving local-first behavior and graceful failures.
    """

    settings: Settings = field(default_factory=Settings)
    event_bus: EventBus | None = None
    registry: ServiceRegistry | None = None

    auth: TwitchAuthService | None = None
    obs: OBSConnector | None = None
    logger: StreamLogger | None = None
    ai: AiProducerV2 | None = None
    reporter: ReportGenerator | None = None
    discord_reporter: DiscordReporter | None = None
    chat: TwitchChatService | None = None
    twitch_api: TwitchApiService | None = None
    eventsub: EventSubService | None = None

    def __post_init__(self) -> None:
        self.event_bus = self.event_bus or EventBus()
        self.registry = self.registry or ServiceRegistry()

        self.auth = TwitchAuthService(
            self.settings.twitch_client_id,
            self.settings.twitch_client_secret,
            self.settings.twitch_redirect_uri,
        )
        self.obs = OBSConnector(
            self.settings.obs_host,
            self.settings.obs_port,
            self.settings.obs_password,
        )
        self.logger = StreamLogger()
        self.ai = AiProducerV2(
            self.settings.ai_provider,
            self.settings.openai_api_key,
            self.settings.openai_model,
        )
        self.reporter = ReportGenerator(
            self.settings.ai_provider,
            self.settings.openai_api_key,
            self.settings.openai_model,
        )
        self.discord_reporter = DiscordReporter()

        self.registry.register_many(
            {
                "settings": self.settings,
                "event_bus": self.event_bus,
                "auth": self.auth,
                "obs": self.obs,
                "logger": self.logger,
                "ai": self.ai,
                "reporter": self.reporter,
            }
        )

        self.event_bus.publish("application.services_ready", {"settings": self.settings})

    def start_twitch_runtime(self) -> bool:
        """Create the Twitch runtime services lazily when the user enables them."""
        if not self.auth or not self.auth.ensure_access_token():
            return False

        self.chat = TwitchChatService(
            self.settings.twitch_channel,
            self.settings.twitch_channel,
            self.auth.oauth_token,
        )
        self.twitch_api = TwitchApiService(
            self.settings.twitch_client_id,
            self.settings.twitch_channel,
            self.auth.access_token,
        )
        self.eventsub = EventSubService(
            self.settings.twitch_client_id,
            self.settings.twitch_channel,
            self.auth.access_token,
        )

        self.registry.register_many(
            {
                "chat": self.chat,
                "twitch_api": self.twitch_api,
                "eventsub": self.eventsub,
            }
        )

        self.event_bus.publish("application.twitch_runtime_started", {"services": self})
        return True

    def get(self, name: str, default: Any = None) -> Any:
        return self.registry.get(name, default)
