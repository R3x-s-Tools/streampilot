from .architecture import EventBus, ServiceRegistry
from .connectors import Connector, ConnectorEvent, ConnectorStatus
from .mission_control import MissionControlReadModel, MissionControlState
from .secret_store import (
    FileSecretStore,
    KeyringSecretStore,
    MigratingSecretStore,
    SecretStore,
    SecretStoreError,
    create_twitch_secret_store,
)

__all__ = [
    "EventBus",
    "ServiceRegistry",
    "FileSecretStore",
    "KeyringSecretStore",
    "MigratingSecretStore",
    "SecretStore",
    "SecretStoreError",
    "create_twitch_secret_store",
    "SessionController",
    "Connector",
    "ConnectorEvent",
    "ConnectorStatus",
    "MissionControlReadModel",
    "MissionControlState",
]


def __getattr__(name: str):
    if name == "SessionController":
        from .session_controller import SessionController

        return SessionController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
