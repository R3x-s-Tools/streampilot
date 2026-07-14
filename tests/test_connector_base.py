from core.connectors.base import ConnectionState, Connector, ConnectorStatus


class MockConnector(Connector):
    """Mock connector for testing the base interface."""

    def __init__(self):
        super().__init__(name="MockConnector")
        self._connected = False
        self._should_fail = False

    def connect(self) -> bool:
        if self._should_fail:
            self._status = ConnectorStatus(
                state=ConnectionState.ERROR, connected=False, error="Connection failed"
            )
            return False
        self._connected = True
        self._status = ConnectorStatus(state=ConnectionState.CONNECTED, connected=True)
        return True

    def disconnect(self) -> None:
        self._connected = False
        self._status = ConnectorStatus(state=ConnectionState.DISCONNECTED, connected=False)

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> ConnectorStatus:
        return self._status


def test_connector_initialization():
    connector = MockConnector()
    assert connector.name == "MockConnector"
    assert connector._status.state == ConnectionState.DISCONNECTED


def test_connector_connect_success():
    connector = MockConnector()
    result = connector.connect()
    assert result is True
    assert connector.is_connected() is True
    status = connector.get_status()
    assert status.state == ConnectionState.CONNECTED
    assert status.connected is True


def test_connector_connect_failure():
    connector = MockConnector()
    connector._should_fail = True
    result = connector.connect()
    assert result is False
    assert connector.is_connected() is False
    status = connector.get_status()
    assert status.state == ConnectionState.ERROR
    assert status.connected is False
    assert status.error == "Connection failed"


def test_connector_disconnect():
    connector = MockConnector()
    connector.connect()
    assert connector.is_connected() is True

    connector.disconnect()
    assert connector.is_connected() is False
    status = connector.get_status()
    assert status.state == ConnectionState.DISCONNECTED


def test_connector_health_check():
    connector = MockConnector()
    assert connector.health_check() is False

    connector.connect()
    assert connector.health_check() is True

    connector.disconnect()
    assert connector.health_check() is False


def test_connector_status_metadata():
    connector = MockConnector()
    connector.connect()
    status = connector.get_status()
    assert status.metadata is not None
    assert isinstance(status.metadata, dict)


def test_connector_repr():
    connector = MockConnector()
    connector.connect()
    repr_str = repr(connector)
    assert "MockConnector" in repr_str
    assert "connected" in repr_str


def test_connector_status_initial_state():
    status = ConnectorStatus()
    assert status.state == ConnectionState.DISCONNECTED
    assert status.connected is False
    assert status.error == ""
    assert status.last_error == ""
    assert status.metadata is not None


def test_connector_status_with_values():
    status = ConnectorStatus(
        state=ConnectionState.CONNECTED,
        connected=True,
        error="",
        last_error="",
        metadata={"key": "value"},
    )
    assert status.state == ConnectionState.CONNECTED
    assert status.connected is True
    assert status.metadata["key"] == "value"


def test_connection_state_enum():
    assert ConnectionState.DISCONNECTED.value == "disconnected"
    assert ConnectionState.CONNECTING.value == "connecting"
    assert ConnectionState.CONNECTED.value == "connected"
    assert ConnectionState.ERROR.value == "error"
