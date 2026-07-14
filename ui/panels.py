from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MissionControlPanel(QFrame):
    """A lightweight Mission Control surface for stream health and actions."""

    def __init__(self, title: str = "🛰 Mission Control") -> None:
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
            }
            QLabel {
                border: none;
            }
            """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        outer.addWidget(title_label)

        self.summary_label = QLabel("Ready to connect Twitch, OBS, and the producer workflow.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 11px; color: #cfd8e3; padding: 0;")
        outer.addWidget(self.summary_label)

        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(6)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self.cards_layout)

    def add_status_card(self, card: QWidget) -> None:
        self.cards_layout.addWidget(card)

    def set_summary(self, text: str) -> None:
        self.summary_label.setText(text)


class ProducerConsolePanel(QFrame):
    """A reusable console panel for the producer experience."""

    def __init__(self, title: str = "🎛 Producer Console") -> None:
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel {
                border: none;
            }
            """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.layout.addWidget(title_label)

        self.live_status_box = QLabel(
            "Not live yet. Start Twitch services to populate stream status."
        )
        self.live_status_box.setWordWrap(True)
        self.live_status_box.setAlignment(self.live_status_box.alignment())
        self.live_status_box.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 12px;
                border: 1px solid #444;
                border-radius: 8px;
                background-color: #111;
            }
            """)
        self.layout.addWidget(QLabel("Live Status"))
        self.layout.addWidget(self.live_status_box)

    def add_section(self, label: str, widget: QWidget) -> None:
        self.layout.addWidget(QLabel(label))
        self.layout.addWidget(widget)
