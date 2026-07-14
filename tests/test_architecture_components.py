from core.architecture import EventBus, ServiceRegistry


def test_event_bus_delivers_payloads() -> None:
    bus = EventBus()
    received: list[str] = []

    bus.subscribe("topic", received.append)
    bus.publish("topic", "hello")

    assert received == ["hello"]


def test_service_registry_resolves_registered_services() -> None:
    registry = ServiceRegistry()
    marker = object()

    registry.register("marker", marker)

    assert registry.get("marker") is marker
    assert registry.has("marker") is True
