import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame

from ui.components import LogPanel, StatusCard
from ui.panels import MissionControlPanel, ProducerConsolePanel

APP = QApplication.instance() or QApplication([])


def test_console_panel_exposes_live_status_widget() -> None:
    panel = ProducerConsolePanel()

    assert panel.live_status_box is not None


def test_status_card_supports_value_updates() -> None:
    card = StatusCard("Test", "before")
    card.set_value("after")

    assert card.value_label.text() == "after"


def test_log_panel_is_read_only() -> None:
    panel = LogPanel()

    assert panel.isReadOnly() is True


def test_console_panel_uses_frame_container() -> None:
    panel = ProducerConsolePanel()

    assert isinstance(panel, QFrame)


def test_mission_control_panel_accepts_status_cards() -> None:
    panel = MissionControlPanel()
    card = StatusCard("Health", "ok")

    panel.add_status_card(card)

    assert panel.cards_layout.count() == 1
    assert panel.cards_layout.itemAt(0).widget() is card
