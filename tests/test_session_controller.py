from core.session_controller import SessionController


def test_session_controller_bootstraps_services(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STREAMPILOT_SECRET_STORE", "file")
    controller = SessionController()

    assert controller.services is not None
    assert controller.registry is not None
    assert controller.auth is not None
    assert controller.obs is not None
    assert controller.logger is not None
    assert controller.ai is not None
    assert controller.reporter is not None
