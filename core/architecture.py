from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventBus:
    """A small event bus for decoupled, explicit app events.

    The bus keeps the application layered by letting services and UI components
    communicate through topics instead of direct object coupling.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        self._subscribers[topic].append(callback)

        def unsubscribe() -> None:
            handlers = self._subscribers.get(topic, [])
            if callback in handlers:
                handlers.remove(callback)

        return unsubscribe

    def publish(self, topic: str, payload: Any = None) -> None:
        for callback in list(self._subscribers.get(topic, [])):
            try:
                callback(payload)
            except Exception:
                # Fail gracefully: a single listener should not take down the app.
                continue

    def clear(self) -> None:
        self._subscribers.clear()


class ServiceRegistry:
    """A simple registry for application services and infrastructure objects."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def register_many(self, services: dict[str, Any]) -> None:
        for name, service in services.items():
            self.register(name, service)

    def get(self, name: str, default: Any = None) -> Any:
        return self._services.get(name, default)

    def has(self, name: str) -> bool:
        return name in self._services

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __getitem__(self, name: str) -> Any:
        return self._services[name]

    def items(self) -> list[tuple[str, Any]]:
        return list(self._services.items())
