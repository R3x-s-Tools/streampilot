from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConnectionState(Enum):
    """Represents the connection state of a connector."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ConnectorStatus:
    """Status information for a connector."""
    state: ConnectionState = ConnectionState.DISCONNECTED
    connected: bool = False
    error: str = ""
    last_error: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Connector(ABC):
    """
    Base class for all connectors.

    A connector communicates with one external system (e.g., OBS, Twitch, Discord).
    Connectors establish connections, authenticate, monitor health, receive external events,
    translate them into StreamPilot events, and shut down gracefully.

    Per SPS-005, connectors do NOT:
    - Perform analytics
    - Generate reports
    - Make UI decisions
    - Store long-term state
    - Directly access unrelated connectors
    """

    def __init__(self, name: str):
        self.name = name
        self._status = ConnectorStatus()

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the external system.

        Returns:
            True if connection successful, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully disconnect from the external system."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the connector is currently connected."""
        pass

    @abstractmethod
    def get_status(self) -> ConnectorStatus:
        """
        Get the current status of the connector.

        Returns:
            ConnectorStatus with current state and error information.
        """
        pass

    def health_check(self) -> bool:
        """
        Perform a health check on the connection.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        return self.is_connected()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, state={self._status.state.value})"
