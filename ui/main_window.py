from __future__ import annotations

import time
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai.producer_v2 import AiProducerV2
from analytics.logger import StreamLogger
from core.architecture import EventBus
from core.config import Settings
from core.session_controller import SessionController
from reports.generator import ReportGenerator
from services.application_services import ApplicationServices
from services.eventsub_service import EventSubService
from services.obs_service import ObsService, ObsSnapshot
from services.twitch_api import TwitchApiService
from services.twitch_auth import TwitchAuthService
from services.twitch_chat import TwitchChatService
from ui.components import LogPanel, SectionLabel, StatusCard
from ui.panels import MissionControlPanel, ProducerConsolePanel
from ui.session_presenter import SessionPresenter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.setWindowTitle("Dad_R3x Command Center Pro v0.2 Producer Console")

        from PySide6.QtWidgets import QApplication as _QApplication
        screen = _QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.resize(int(geo.width() * 0.92), int(geo.height() * 0.92))
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )
        else:
            self.resize(1500, 950)

        self.event_bus = EventBus()
        self.controller = SessionController(settings=self.settings, event_bus=self.event_bus)
        self.services = self.controller.services
        self.settings = self.controller.settings
        self.auth = self.controller.auth
        self.obs = self.controller.obs
        self.logger = self.controller.logger
        self.ai = self.controller.ai
        self.reporter = self.controller.reporter

        self.chat = self.controller.chat
        self.twitch_api = self.controller.twitch_api
        self.eventsub = self.controller.eventsub
        self.registry = self.controller.registry
        self.discord_reporter = self.controller.discord_reporter
        self.presenter = SessionPresenter(self.settings, self.logger)

        self.latest_obs = ObsSnapshot()
        self.latest_twitch = None
        self.recent_chat = []

        self.last_twitch_poll = 0
        self.last_ai_refresh = 0
        self.last_ai_notes_text = ""
        self.last_ai_timeline_post = 0
        self.ai_timeline_min_seconds = 180
        self.ai_force_repeat_seconds = 600

        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.settings.obs_poll_seconds * 1000)

    def _build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(4)
        self.setCentralWidget(root)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("🦖 Dad_R3x Command Center Pro v0.2")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        root_layout.addLayout(header)

        self.status_panel = MissionControlPanel()
        self.auth_card = self._status_card("Twitch Auth", "Checking...")
        self.obs_card = self._status_card("OBS", "Waiting...")
        self.twitch_card = self._status_card("Twitch", "Not started")
        self.ai_card = self._status_card("AI Producer", "Waiting...")

        for card in [self.auth_card, self.obs_card, self.twitch_card, self.ai_card]:
            self.status_panel.add_status_card(card["box"])

        self.status_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root_layout.addWidget(self.status_panel)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        for label, handler in [
            ("Login with Twitch", self._login),
            ("Refresh Token", self._refresh_token),
            ("Start Twitch", self._start_twitch_services),
            ("Open Twitch Preview", self._open_preview),
            ("Mark Clip Moment", self._manual_clip),
            ("Generate Reports", self._reports),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            controls.addWidget(button)

        controls.addStretch()
        root_layout.addLayout(controls)

        main_splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(main_splitter, stretch=1)

        # Left side: signal-first producer console.
        console_panel = ProducerConsolePanel()
        console_layout = console_panel.layout

        self.live_status_box = console_panel.live_status_box
        console_layout.addWidget(SectionLabel("What to do next"))
        self.action_box = LogPanel("AI Producer suggestions will appear here.")
        console_layout.addWidget(self.action_box, stretch=2)

        console_layout.addWidget(SectionLabel("High-signal moments"))
        self.moments_box = LogPanel(
            "Follows, spikes, chat bursts, and clip markers will appear here."
        )
        console_layout.addWidget(self.moments_box, stretch=2)

        console_layout.addWidget(SectionLabel("AI timeline"))
        self.ai_timeline_box = LogPanel("AI timeline entries will appear here.")
        console_layout.addWidget(self.ai_timeline_box, stretch=3)

        main_splitter.addWidget(console_panel)

        # Right side: raw/support data.
        self.tabs = QTabWidget()
        self.chat_box = self._tab_text("💬 Chat")
        self.events_box = self._tab_text("⭐ Events")
        self.analytics_box = self._tab_text("📈 Analytics")
        self.system_log_box = self._tab_text("🛠 System Log")
        self.raw_ai_box = self._tab_text("🤖 Raw AI Output")

        main_splitter.addWidget(self.tabs)
        main_splitter.setSizes([620, 880])

        self.footer = QLabel(f"Session log: {self.logger.session_file}")
        self.footer.setMaximumHeight(20)
        self.footer.setStyleSheet("font-size: 11px; color: #888;")
        root_layout.addWidget(self.footer)

    def _status_card(self, title: str, value: str) -> dict:
        box = StatusCard(title, value)
        return {"box": box, "value": box.value_label}

    def _tab_text(self, title: str) -> QTextEdit:
        box = LogPanel()
        self.tabs.addTab(box, title)
        return box

    def _append_system(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.system_log_box.append(f"[{stamp}] {message}")
        self.event_bus.publish("ui.system_message", message)

    def _append_moment(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.moments_box.append(f"[{stamp}] {message}")
        self.events_box.append(f"[{stamp}] {message}")

    def _append_ai_timeline(self, notes: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.ai_timeline_box.append(f"[{stamp}]\n{notes}\n")

    def _login(self):
        self._append_system("Starting Twitch login flow...")
        ok = self.auth.login_interactive()
        QMessageBox.information(
            self,
            "Twitch Login",
            "Login complete." if ok else f"Login failed: {self.auth.last_error}",
        )
        self._update_auth_status()

    def _refresh_token(self):
        token = self.auth.refresh()
        QMessageBox.information(
            self,
            "Twitch Token",
            "Token refreshed." if token else f"Refresh failed: {self.auth.last_error}",
        )
        self._update_auth_status()

    def _start_twitch_services(self):
        if not self.controller.start_twitch_runtime():
            QMessageBox.warning(self, "Twitch", "Login with Twitch first.")
            return

        self.chat = self.controller.chat
        self.twitch_api = self.controller.twitch_api
        self.eventsub = self.controller.eventsub

        self.chat.start()
        self.eventsub.start()

        self._append_system("Twitch chat and EventSub services started.")
        QMessageBox.information(self, "Twitch", "Twitch services started.")

    def _open_preview(self):
        webbrowser.open(f"https://www.twitch.tv/{self.settings.twitch_channel}")

    def _tick(self):
        state = self.presenter.tick(self.auth, self.obs, self.chat, self.twitch_api, self.eventsub, self.ai)
        self._apply_presenter_state(state)
        self._apply_presenter_updates()

    def _apply_presenter_state(self, state: dict):
        self.summary = state.get("summary", {})
        self.analytics_text = state.get("analytics_text", "")
        self.ai_notes = state.get("ai_notes", "")
        self.auth_card["value"].setText(self.presenter.auth_display)
        self.obs_card["value"].setText(self.presenter.obs_display)
        self.twitch_card["value"].setText(self.presenter.twitch_display)
        self.live_status_box.setText(self.presenter.live_status)
        self.status_panel.set_summary(self.presenter.live_status or "Waiting for updates.")
        self.analytics_box.setPlainText(self.presenter.analytics_text)
        self.action_box.setPlainText(self.presenter.ai_notes)
        self.raw_ai_box.setPlainText(self.presenter.ai_notes)
        self.ai_card["value"].setText(f"Updated {datetime.now().strftime('%H:%M:%S')}")

    def _apply_presenter_updates(self):
        for message in self.presenter.chat_updates:
            stamp = datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S")
            self.chat_box.append(f"[{stamp}] {message.username}: {message.message}")

        for message in self.presenter.moment_updates:
            self._append_moment(message)

        for event in self.presenter.event_updates:
            stamp = datetime.fromtimestamp(event.timestamp_epoch).strftime("%H:%M:%S")
            line = f"[{stamp}] {event.message}"
            self.events_box.append(line)
            self.moments_box.append(line)

        for note in self.presenter.ai_timeline_updates:
            self.ai_timeline_box.append(note)

    def _manual_clip(self):
        self._append_system("Manual clip marker pressed.")
        self._append_moment("Manual clip marker pressed.")
        if self.logger:
            self.logger.add_event("manual_clip_marker", 8, "Manual clip marker pressed.", {"scene": "manual"})
        QMessageBox.information(self, "Clip Moment", "Clip marker logged.")

    def _reports(self):
        self._append_system("Generating reports...")
        try:
            payload = self.logger.summary() if self.logger else {}
            highlight, analytics = self.reporter.generate(payload)
            self._append_system(f"Reports generated: {highlight} and {analytics}")

            if self.settings.report_to_discord:
                if self.discord_reporter and self.discord_reporter.enabled:
                    try:
                        self.discord_reporter.send_markdown_report(
                            report_path=analytics,
                            summary=payload,
                            attach_report=True,
                        )
                        self._append_system("Discord report sent successfully.")
                    except Exception as exc:
                        self._append_system(f"Discord report failed: {exc}")
                        QMessageBox.warning(self, "Discord Report", f"Report generated, but Discord delivery failed:\n{exc}")
                else:
                    self._append_system("REPORT_TO_DISCORD is enabled, but Discord webhook is not configured.")
                    QMessageBox.warning(
                        self,
                        "Discord Report",
                        "Report generated, but Discord webhook is not configured. Set DISCORD_REPORT_WEBHOOK_URL in your .env.",
                    )

            QMessageBox.information(self, "Reports", f"Reports saved:\n{highlight}\n{analytics}")
        except Exception as exc:  # pragma: no cover - UI fallback path
            self._append_system(f"Report generation failed: {exc}")
            QMessageBox.critical(self, "Reports", f"Report generation failed: {exc}")

    def _update_auth_status(self):
        if self.auth and self.auth.oauth_token:
            self.auth_card["value"].setText("Connected")
        else:
            self.auth_card["value"].setText("Not connected")