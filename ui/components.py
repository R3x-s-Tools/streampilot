from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QTextEdit, QVBoxLayout


class StatusCard(QFrame):
    """A small reusable status card for service health display."""

    def __init__(self, title: str, value: str = "") -> None:
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setMaximumHeight(60)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(1)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 11px;")
        self.value_label.setWordWrap(False)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class LogPanel(QTextEdit):
    """A read-only text panel used for system logs and moments."""

    def __init__(self, placeholder: str = "") -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("QTextEdit { font-size: 15px; font-weight: 500; padding: 10px; }")


class SectionLabel(QLabel):
    """A lightweight label with standard top spacing for UI sections."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setAlignment(Qt.AlignTop)
