from connectors.obs_connector import OBSConnector
from core.architecture import EventBus
from core.connectors import ConnectorEvent
from core.mission_control import MissionControlReadModel
from services.application_services import ApplicationServices
from services.obs_service import ObsSnapshot


class FakeObsService:
    def __init__(self, snapshot: ObsSnapshot) -> None:
        self._snapshot = snapshot
        self.last_error = snapshot.error
        self.client = None

    def connect(self) -> None:
        self.client = object()

    def snapshot(self) -> ObsSnapshot:
        return self._snapshot


def test_read_model_updates_from_normalized_obs_event() -> None:
    bus = EventBus()
    read_model = MissionControlReadModel(bus)
    connector = OBSConnector(
        "localhost",
        4455,
        "password",
        event_sink=lambda event: bus.publish("connector.status", event),
        obs_service=FakeObsService(
            ObsSnapshot(connected=True, streaming=True, current_scene="Gameplay")
        ),
    )

    connector.get_snapshot()

    assert read_model.state.connector_statuses["obs"].connected is True
    assert read_model.state.obs_snapshot["streaming"] is True
    assert read_model.state.obs_snapshot["current_scene"] == "Gameplay"


def test_application_services_publish_obs_specific_and_generic_topics(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STREAMPILOT_SECRET_STORE", "file")
    bus = EventBus()
    services = ApplicationServices(event_bus=bus)
    services.obs._obs_service = FakeObsService(ObsSnapshot(connected=True, fps=60.0))
    generic: list[ConnectorEvent] = []
    specific: list[ConnectorEvent] = []
    bus.subscribe("connector.status", generic.append)
    bus.subscribe("connector.obs.status", specific.append)

    snapshot = services.refresh_obs()

    assert snapshot.connected is True
    assert len(generic) == 1
    assert len(specific) == 1
    assert services.mission_control.state.obs_snapshot["fps"] == 60.0
