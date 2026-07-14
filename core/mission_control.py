from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.architecture import EventBus
from core.connectors import ConnectorEvent, ConnectorStatus


@dataclass(frozen=True)
class MissionControlState:
    """Read-only operational state assembled from normalized connector events."""

    connector_statuses: dict[str, ConnectorStatus] = field(default_factory=dict)
    obs_snapshot: dict[str, Any] = field(default_factory=dict)
    updated_at: float = 0.0


class MissionControlReadModel:
    """Build Mission Control state without depending on connector implementations."""

    def __init__(self, event_bus: EventBus) -> None:
        self.state = MissionControlState()
        self._unsubscribe = event_bus.subscribe("connector.status", self._on_connector_status)

    def _on_connector_status(self, event: ConnectorEvent) -> None:
        statuses = dict(self.state.connector_statuses)
        statuses[event.connector] = event.status
        obs_snapshot = self.state.obs_snapshot
        if event.connector == "obs":
            obs_snapshot = dict(event.payload)
        self.state = MissionControlState(
            connector_statuses=statuses,
            obs_snapshot=obs_snapshot,
            updated_at=event.occurred_at,
        )

    def close(self) -> None:
        self._unsubscribe()
