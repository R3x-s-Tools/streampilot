from __future__ import annotations

from typing import Any

from core.architecture import EventBus
from core.config import Settings
from services.application_services import ApplicationServices


class SessionController:
    """Coordinate the app runtime without letting the UI own service lifecycle."""

    def __init__(
        self,
        settings: Settings | None = None,
        event_bus: EventBus | None = None,
        services: ApplicationServices | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.event_bus = event_bus or EventBus()
        self.services = services or ApplicationServices(settings=self.settings, event_bus=self.event_bus)

        self.auth = self.services.auth
        self.obs = self.services.obs
        self.logger = self.services.logger
        self.ai = self.services.ai
        self.reporter = self.services.reporter
        self.discord_reporter = self.services.discord_reporter
        self.registry = self.services.registry

        self.chat = None
        self.twitch_api = None
        self.eventsub = None

    def start_twitch_runtime(self) -> bool:
        started = self.services.start_twitch_runtime()
        if started:
            self.chat = self.services.chat
            self.twitch_api = self.services.twitch_api
            self.eventsub = self.services.eventsub
        return started

    def get_service(self, name: str, default: Any = None) -> Any:
        return self.services.get(name, default)
