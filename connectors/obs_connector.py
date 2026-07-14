from __future__ import annotations

import time
from typing import Any

from core.connectors.base import Connector, ConnectorStatus, ConnectionState
from services.obs_service import ObsService, ObsSnapshot


class OBSConnector(Connector):
    """
    OBS WebSocket connector implementing the Connector framework.

    This connector wraps the existing ObsService to provide a standardized
    connector interface while maintaining full backwards compatibility.

    Per SPS-005, this connector:
    - Establishes connections to OBS
    - Monitors health
    - Translates OBS events to StreamPilot events
    - Does NOT perform analytics, generate reports, or make UI decisions
    """

    def __init__(self, host: str, port: int, password: str):
        super().__init__(name="OBS")
        self.host = host
        self.port = port
        self.password = password
        
        # Wrap the existing ObsService for backwards compatibility
        self._obs_service = ObsService(host, port, password)
        
        # Track connection state
        self._connection_attempts = 0
        self._last_successful_connection = 0.0

    def connect(self) -> bool:
        """Establish connection to OBS WebSocket."""
        try:
            self._connection_attempts += 1
            self._obs_service.connect()
            
            # Verify connection by taking a snapshot
            snapshot = self._obs_service.snapshot()
            
            if snapshot.connected:
                self._status = ConnectorStatus(
                    state=ConnectionState.CONNECTED,
                    connected=True,
                    metadata={
                        "host": self.host,
                        "port": self.port,
                        "connection_attempts": self._connection_attempts,
                    }
                )
                self._last_successful_connection = time.time()
                return True
            else:
                self._status = ConnectorStatus(
                    state=ConnectionState.ERROR,
                    connected=False,
                    error=snapshot.error,
                    last_error=snapshot.error,
                    metadata={"host": self.host, "port": self.port}
                )
                return False
                
        except Exception as exc:
            self._status = ConnectorStatus(
                state=ConnectionState.ERROR,
                connected=False,
                error=str(exc),
                last_error=str(exc),
                metadata={"host": self.host, "port": self.port}
            )
            return False

    def disconnect(self) -> None:
        """Gracefully disconnect from OBS."""
        self._obs_service.client = None
        self._status = ConnectorStatus(
            state=ConnectionState.DISCONNECTED,
            connected=False,
            metadata={"host": self.host, "port": self.port}
        )

    def is_connected(self) -> bool:
        """Check if currently connected to OBS."""
        return self._obs_service.snapshot().connected

    def get_status(self) -> ConnectorStatus:
        """Get current connector status."""
        snapshot = self._obs_service.snapshot()
        
        if snapshot.connected:
            state = ConnectionState.CONNECTED
        elif snapshot.error and "Retrying in" in snapshot.error:
            state = ConnectionState.CONNECTING
        else:
            state = ConnectionState.ERROR
            
        self._status = ConnectorStatus(
            state=state,
            connected=snapshot.connected,
            error=snapshot.error,
            last_error=self._obs_service.last_error,
            metadata={
                "host": self.host,
                "port": self.port,
                "current_scene": snapshot.current_scene,
                "streaming": snapshot.streaming,
                "recording": snapshot.recording,
                "fps": snapshot.fps,
                "cpu_usage": snapshot.cpu_usage,
                "memory_usage_mb": snapshot.memory_usage_mb,
                "connection_attempts": self._connection_attempts,
                "last_successful_connection": self._last_successful_connection,
            }
        )
        
        return self._status

    def get_snapshot(self) -> ObsSnapshot:
        """
        Get the current OBS snapshot.
        
        This method provides direct access to the ObsSnapshot for backwards
        compatibility with existing code that depends on ObsService.
        """
        return self._obs_service.snapshot()

    def health_check(self) -> bool:
        """Perform health check by verifying OBS connection."""
        snapshot = self._obs_service.snapshot()
        return snapshot.connected and not snapshot.error

    @property
    def obs_service(self) -> ObsService:
        """
        Provide access to the underlying ObsService for backwards compatibility.
        
        This property allows existing code to continue using the ObsService
        interface while we migrate to the Connector framework.
        """
        return self._obs_service
