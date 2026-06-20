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
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai.producer_v2 import AiProducerV2
from analytics.logger import StreamLogger
from core.config import Settings
from reports.generator import ReportGenerator
from services.eventsub_service import EventSubService
from services.obs_service import ObsService, ObsSnapshot
from services.twitch_api import TwitchApiService
from services.twitch_auth import TwitchAuthService
from services.twitch_chat import TwitchChatService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.setWindowTitle("Dad_R3x Command Center Pro v0.2 Producer Console")
        self.resize(1500, 950)

        self.auth = TwitchAuthService(
            self.settings.twitch_client_id,
            self.settings.twitch_client_secret,
            self.settings.twitch_redirect_uri,
        )
        self.obs = ObsService(
            self.settings.obs_host,
            self.settings.obs_port,
            self.settings.obs_password,
        )
        self.logger = StreamLogger()
        self.ai = AiProducerV2(
            self.settings.ai_provider,
            self.settings.openai_api_key,
            self.settings.openai_model,
        )
        self.reporter = ReportGenerator(
            self.settings.ai_provider,
            self.settings.openai_api_key,
            self.settings.openai_model,
        )

        self.chat = None
        self.twitch_api = None
        self.eventsub = None

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
        self.setCentralWidget(root)

        header = QHBoxLayout()
        title = QLabel("🦖 Dad_R3x Command Center Pro v0.2")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        root_layout.addLayout(header)

        status_row = QHBoxLayout()
        self.auth_card = self._status_card("Twitch Auth", "Checking...")
        self.obs_card = self._status_card("OBS", "Waiting...")
        self.twitch_card = self._status_card("Twitch", "Not started")
        self.ai_card = self._status_card("AI Producer", "Waiting...")

        for card in [self.auth_card, self.obs_card, self.twitch_card, self.ai_card]:
            status_row.addWidget(card["box"])

        root_layout.addLayout(status_row)

        controls = QHBoxLayout()
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
        console_panel = QGroupBox("🎛 Producer Console")
        console_layout = QVBoxLayout(console_panel)

        self.live_status_box = QLabel(
            "Not live yet. Start Twitch services to populate stream status."
        )
        self.live_status_box.setWordWrap(True)
        self.live_status_box.setAlignment(Qt.AlignTop)
        self.live_status_box.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 12px;
                border: 1px solid #444;
                border-radius: 8px;
                background-color: #111;
            }
            """)
        console_layout.addWidget(QLabel("Live Status"))
        console_layout.addWidget(self.live_status_box)

        console_layout.addWidget(QLabel("What to do next"))
        self.action_box = QTextEdit()
        self.action_box.setReadOnly(True)
        self.action_box.setPlaceholderText("AI Producer suggestions will appear here.")
        self.action_box.setStyleSheet(
            "QTextEdit { font-size: 15px; font-weight: 500; padding: 10px; }"
        )
        console_layout.addWidget(self.action_box, stretch=2)

        console_layout.addWidget(QLabel("High-signal moments"))
        self.moments_box = QTextEdit()
        self.moments_box.setReadOnly(True)
        self.moments_box.setPlaceholderText(
            "Follows, spikes, chat bursts, and clip markers will appear here."
        )
        console_layout.addWidget(self.moments_box, stretch=2)

        console_layout.addWidget(QLabel("AI timeline"))
        self.ai_timeline_box = QTextEdit()
        self.ai_timeline_box.setReadOnly(True)
        self.ai_timeline_box.setPlaceholderText("AI timeline entries will appear here.")
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
        root_layout.addWidget(self.footer)

    def _status_card(self, title: str, value: str) -> dict:
        box = QFrame()
        box.setFrameShape(QFrame.StyledPanel)
        box.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel {
                border: none;
            }
            """)
        layout = QVBoxLayout(box)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        value_label = QLabel(value)
        value_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return {"box": box, "value": value_label}

    def _tab_text(self, title: str) -> QTextEdit:
        box = QTextEdit()
        box.setReadOnly(True)
        box.setLineWrapMode(QTextEdit.WidgetWidth)
        self.tabs.addTab(box, title)
        return box

    def _append_system(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.system_log_box.append(f"[{stamp}] {message}")

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
        token = self.auth.ensure_access_token()

        if not token:
            QMessageBox.warning(self, "Twitch", "Login with Twitch first.")
            return

        self.chat = TwitchChatService(
            self.settings.twitch_channel,
            self.settings.twitch_channel,
            self.auth.oauth_token,
        )
        self.twitch_api = TwitchApiService(
            self.settings.twitch_client_id,
            self.settings.twitch_channel,
            self.auth.access_token,
        )
        self.eventsub = EventSubService(
            self.settings.twitch_client_id,
            self.settings.twitch_channel,
            self.auth.access_token,
        )

        self.chat.start()
        self.eventsub.start()

        self._append_system("Twitch chat and EventSub services started.")
        QMessageBox.information(self, "Twitch", "Twitch services started.")

    def _open_preview(self):
        webbrowser.open(f"https://www.twitch.tv/{self.settings.twitch_channel}")

    def _tick(self):
        self._update_auth_status()
        self._update_obs()
        self._update_chat()
        self._update_twitch_api()
        self._update_eventsub()
        self._update_live_status()
        self._update_analytics_tab()
        self._auto_ai_notes()

    def _update_auth_status(self):
        self.auth.ensure_access_token()
        validation = self.auth.validate()

        if validation:
            scopes = " ".join(validation.get("scopes", []))
            self.auth_card["value"].setText(f"{self.auth.status}\nScopes: {scopes}")
        else:
            self.auth_card["value"].setText(self.auth.status)

    def _update_obs(self):
        self.latest_obs = self.obs.snapshot()

        if self.latest_obs.connected:
            live = "LIVE" if self.latest_obs.streaming else "Not streaming"
            self.obs_card["value"].setText(
                f"{live}\nScene: {self.latest_obs.current_scene}\n"
                f"FPS: {self._fmt(self.latest_obs.fps)} | CPU: {self._fmt(self.latest_obs.cpu_usage)}%"
            )
        else:
            self.obs_card["value"].setText(f"Disconnected\n{self.latest_obs.error}")

        self.logger.add_obs(self.latest_obs)

    def _update_chat(self):
        if not self.chat:
            return

        messages = self.chat.drain()

        if not messages:
            return

        self.recent_chat.extend(messages)
        self.recent_chat = self.recent_chat[-50:]
        self.logger.add_chat(messages)

        for message in messages:
            stamp = datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S")
            self.chat_box.append(f"[{stamp}] {message.username}: {message.message}")

            profile = self.logger.viewer_memory.get_profile(message.username)
            if profile and profile.total_messages == 1:
                self._append_moment(f"🌱 First-time chatter: {message.username}")
            elif profile and profile.is_regular and profile.total_messages in {25, 50, 100}:
                self._append_moment(
                    f"⭐ Regular viewer milestone: {message.username} has {profile.total_messages} messages"
                )

    def _update_twitch_api(self):
        if not self.twitch_api:
            return

        if time.time() - self.last_twitch_poll < self.settings.twitch_analytics_seconds:
            return

        self.last_twitch_poll = time.time()
        previous_viewers = None
        if self.latest_twitch:
            previous_viewers = self.latest_twitch.viewer_count

        self.latest_twitch = self.twitch_api.snapshot(self.logger.stream_time())
        self.logger.add_twitch_snapshot(self.twitch_api.to_dict(self.latest_twitch))

        if self.latest_twitch.connected:
            self.twitch_card["value"].setText(
                f"{'LIVE' if self.latest_twitch.live else 'Offline'}\n"
                f"Viewers: {self.latest_twitch.viewer_count}\n"
                f"Game: {self.latest_twitch.game_name or '?'}\n"
                f"Followers: {self.latest_twitch.follower_total if self.latest_twitch.follower_total is not None else '?'}"
            )

            if previous_viewers is not None:
                delta = self.latest_twitch.viewer_count - previous_viewers
                if delta >= 2:
                    self._append_moment(
                        f"📈 Viewer spike: +{delta}, now {self.latest_twitch.viewer_count}"
                    )
                elif delta <= -2:
                    self._append_moment(
                        f"📉 Viewer drop: {delta}, now {self.latest_twitch.viewer_count}"
                    )
        else:
            self.twitch_card["value"].setText(f"API Error\n{self.latest_twitch.error}")

    def _update_eventsub(self):
        if not self.eventsub:
            return

        events = self.eventsub.drain()

        if not events:
            return

        event_dicts = [self.eventsub.to_dict(event) for event in events]
        self.logger.add_twitch_events(event_dicts)

        for event in events:
            stamp = datetime.fromtimestamp(event.timestamp_epoch).strftime("%H:%M:%S")
            line = f"[{stamp}] {event.message}"
            self.events_box.append(line)
            self.moments_box.append(line)
            self.ai_timeline_box.append(f"[{stamp}] Twitch Event\n{event.message}\n")

    def _update_live_status(self):
        obs_line = "OBS: Disconnected"
        if self.latest_obs.connected:
            obs_line = (
                f"OBS: {'LIVE' if self.latest_obs.streaming else 'Not streaming'} | "
                f"Scene: {self.latest_obs.current_scene} | FPS: {self._fmt(self.latest_obs.fps)}"
            )

        twitch_line = "Twitch: Not started"
        if self.latest_twitch:
            twitch_line = (
                f"Twitch: {'LIVE' if self.latest_twitch.live else 'Offline'} | "
                f"Viewers: {self.latest_twitch.viewer_count} | "
                f"Game: {self.latest_twitch.game_name or '?'}"
            )

        summary = self.logger.summary()
        viewers = summary.get("viewer_summary", {})
        top_viewers = summary.get("top_viewers", [])
        top_viewer_line = "Top viewer: none yet"
        if top_viewers:
            top = top_viewers[0]
            top_viewer_line = (
                f"Top viewer: {top.get('username')} | "
                f"Score: {top.get('engagement_score')} | "
                f"Messages: {top.get('total_messages')}"
            )

        self.live_status_box.setText(
            f"{obs_line}\n"
            f"{twitch_line}\n"
            f"Avg viewers: {viewers.get('average_viewers', 0)} | "
            f"Peak: {viewers.get('peak_viewers', 0)}\n"
            f"Human chat: {summary.get('total_chat_messages', 0)} | "
            f"Unique chatters: {summary.get('unique_chatters', 0)} | "
            f"Bot filtered: {summary.get('bot_chat_messages', 0)}\n"
            f"{top_viewer_line}"
        )

    def _update_analytics_tab(self):
        summary = self.logger.summary()
        viewers = summary.get("viewer_summary", {})
        score = summary.get("stream_score", {})
        top_viewers = summary.get("top_viewers", [])

        lines = [
            "Stream Score",
            f"Overall: {score.get('overall', '?')}/100",
            f"Viewer retention: {score.get('viewer_retention', '?')}/100",
            f"Chat engagement: {score.get('chat_engagement', '?')}/100",
            f"Clip potential: {score.get('clip_potential', '?')}/100",
            "",
            "Viewers",
            f"Average: {viewers.get('average_viewers', 0)}",
            f"Peak: {viewers.get('peak_viewers', 0)}",
            f"Low: {viewers.get('low_viewers', 0)}",
            f"Samples: {viewers.get('samples', 0)}",
            "",
            "Engagement",
            f"Human chat messages: {summary.get('total_chat_messages', 0)}",
            f"Unique chatters: {summary.get('unique_chatters', 0)}",
            f"Bot/system filtered: {summary.get('bot_chat_messages', 0)}",
            "",
            "Top Viewers",
        ]

        if top_viewers:
            for viewer in top_viewers[:8]:
                lines.append(
                    f"- {viewer.get('username')} | score {viewer.get('engagement_score')} | "
                    f"messages {viewer.get('total_messages')} | regular {viewer.get('is_regular')}"
                )
        else:
            lines.append("- none yet")

        self.analytics_box.setPlainText("\n".join(lines))

    def _auto_ai_notes(self):
        if time.time() - self.last_ai_refresh < self.settings.ai_refresh_seconds:
            return

        self.last_ai_refresh = time.time()
        self._ai_notes(auto=True)

    def _ai_notes(self, auto: bool = False):
        recent_events = self.logger.twitch_events[-10:]
        recent_highlights = [
            {
                "stream_time": event.stream_time,
                "event_type": event.event_type,
                "score": event.score,
                "reason": event.reason,
            }
            for event in self.logger.events[-10:]
        ]

        notes = self.ai.suggest(
            self.latest_obs,
            self.recent_chat,
            self.latest_twitch,
            recent_events=recent_events,
            recent_highlights=recent_highlights,
            chat_history=self.logger.chat_history,
            viewer_memory=self.logger.viewer_memory,
        )

        self.action_box.setPlainText(notes)
        self.raw_ai_box.setPlainText(notes)
        self.ai_card["value"].setText(f"Updated {datetime.now().strftime('%H:%M:%S')}")

        if self._should_post_ai_timeline(notes, auto=auto):
            self._append_ai_timeline(notes)
            self.last_ai_notes_text = notes.strip()
            self.last_ai_timeline_post = time.time()

    def _should_post_ai_timeline(self, notes: str, auto: bool = False) -> bool:
        clean_notes = notes.strip()

        if not clean_notes:
            return False

        if not auto:
            return True

        if clean_notes != self.last_ai_notes_text:
            return True

        if time.time() - self.last_ai_timeline_post >= self.ai_force_repeat_seconds:
            return True

        return False

    def _manual_clip(self):
        event = self.logger.manual_clip(self.latest_obs.current_scene)
        line = f"[{event.stream_time}] 🎬 Manual clip marker: {self.latest_obs.current_scene}"
        self.events_box.append(line)
        self.moments_box.append(line)
        self.ai_timeline_box.append(f"{line}\n")

    def _reports(self):
        highlight_path, analytics_path = self.reporter.generate(self.logger.summary())
        QMessageBox.information(
            self,
            "Reports generated",
            f"Highlight report:\n{highlight_path}\n\nDeep analytics report:\n{analytics_path}",
        )

    @staticmethod
    def _fmt(value):
        if value is None:
            return "?"
        return f"{value:.2f}" if isinstance(value, float) else str(value)
