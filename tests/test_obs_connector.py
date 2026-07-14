from connectors.obs_connector import OBSConnector
from core.connectors.base import ConnectionState


def test_obs_connector_initialization():
    connector = OBSConnector("localhost", 4455, "password")
    assert connector.name == "OBS"
    assert connector.host == "localhost"
    assert connector.port == 4455
    assert connector.password == "password"
    assert connector._connection_attempts == 0


def test_obs_connector_wraps_obs_service():
    connector = OBSConnector("localhost", 4455, "password")
    assert connector.obs_service is not None
    assert connector.obs_service.host == "localhost"
    assert connector.obs_service.port == 4455
    assert connector.obs_service.password == "password"


def test_obs_connector_get_snapshot_backwards_compatibility():
    connector = OBSConnector("bad-host", 4455, "password")
    connector._obs_service.retry_cooldown_seconds = 30

    snapshot = connector.get_snapshot()
    assert snapshot.connected is False
    assert snapshot.error != ""


def test_obs_connector_is_connected():
    connector = OBSConnector("bad-host", 4455, "password")
    assert connector.is_connected() is False


def test_obs_connector_get_status_disconnected():
    connector = OBSConnector("bad-host", 4455, "password")
    status = connector.get_status()

    assert status.state in [ConnectionState.DISCONNECTED, ConnectionState.ERROR]
    assert status.connected is False
    assert status.metadata is not None
    assert status.metadata["host"] == "bad-host"
    assert status.metadata["port"] == 4455


def test_obs_connector_disconnect():
    connector = OBSConnector("localhost", 4455, "password")
    connector.disconnect()

    assert connector.is_connected() is False
    assert connector._obs_service.client is None
    # After disconnect, get_status may show CONNECTING if snapshot tries to reconnect
    # The important part is that the client is None and is_connected returns False
    status = connector.get_status()
    assert status.connected is False


def test_obs_connector_health_check():
    connector = OBSConnector("bad-host", 4455, "password")
    assert connector.health_check() is False


def test_obs_connector_connection_attempts_tracked():
    connector = OBSConnector("bad-host", 4455, "password")
    assert connector._connection_attempts == 0

    # Attempt connection (will fail)
    connector.connect()
    assert connector._connection_attempts == 1


def test_obs_connector_status_includes_metadata():
    connector = OBSConnector("localhost", 4455, "password")
    status = connector.get_status()

    assert "host" in status.metadata
    assert "port" in status.metadata
    assert "connection_attempts" in status.metadata
