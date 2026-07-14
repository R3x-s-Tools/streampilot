from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from analytics.logger import StreamLogger
from core.config import Settings
from services.obs_service import ObsSnapshot


class SessionPresenter:
    """Owns runtime state aggregation for the main window.

    The presenter keeps the UI thin: it receives live service data and prepares
    the display state without directly owning widgets.
    """

    def __init__(self, settings: Settings, logger: StreamLogger) -> None:
        self.settings = settings
        self.logger = logger
        self.latest_obs = ObsSnapshot()
        self.latest_twitch = None
        self.recent_chat: list[Any] = []
        self.last_twitch_poll = 0.0
        self.last_ai_refresh = 0.0
        self.last_ai_notes_text = ""
        self.last_ai_timeline_post = 0.0
        self.ai_timeline_min_seconds = 180
        self.ai_force_repeat_seconds = 600
        self._last_viewer_event = 0.0
        self.ai_notes = ""
        self.chat_updates: list[Any] = []
        self.event_updates: list[Any] = []
        self.moment_updates: list[str] = []
        self.ai_timeline_updates: list[str] = []

    def tick(
        self, auth: Any, obs: Any, chat: Any, twitch_api: Any, eventsub: Any, ai: Any
    ) -> dict[str, Any]:
        # Clear all per-tick update lists before every cycle so stale entries never repeat.
        self.chat_updates = []
        self.event_updates = []
        self.moment_updates = []
        self.ai_timeline_updates = []

        self._update_auth_status(auth)
        self._update_obs(obs)
        self._update_chat(chat)
        self._update_twitch_api(twitch_api)
        self._update_eventsub(eventsub)
        self._update_live_status()
        return self._update_analytics(ai)

    def _update_auth_status(self, auth: Any) -> None:
        auth.ensure_access_token()
        validation = auth.validate()
        self.auth_status = validation or {"scopes": []}
        self.auth_display = (
            f"{auth.status}\nScopes: {' '.join(self.auth_status.get('scopes', []))}"
            if self.auth_status
            else auth.status
        )

    def _update_obs(self, obs: Any) -> None:
        # Support both ObsService and OBSConnector for backwards compatibility
        if hasattr(obs, "get_snapshot"):
            self.latest_obs = obs.get_snapshot()
        else:
            self.latest_obs = obs.snapshot()
        self.logger.add_obs(self.latest_obs)
        if self.latest_obs.connected:
            live = "LIVE" if self.latest_obs.streaming else "Not streaming"
            self.obs_display = (
                f"{live}\nScene: {self.latest_obs.current_scene}\n"
                f"FPS: {self._fmt(self.latest_obs.fps)} | CPU: {self._fmt(self.latest_obs.cpu_usage)}%"
            )
        else:
            self.obs_display = f"Disconnected\n{self.latest_obs.error}"

    def _update_chat(self, chat: Any) -> None:
        if not chat:
            return
        messages = chat.drain()
        if not messages:
            return
        self.recent_chat.extend(messages)
        self.recent_chat = self.recent_chat[-50:]
        self.logger.add_chat(messages)
        self.chat_updates = messages
        for message in messages:
            profile = self.logger.viewer_memory.get_profile(message.username)
            if profile and profile.total_messages == 1:
                self.moment_updates.append(f"🌱 First-time chatter: {message.username}")
            elif profile and profile.is_regular and profile.total_messages in {25, 50, 100}:
                self.moment_updates.append(
                    f"⭐ Regular viewer milestone: {message.username} has {profile.total_messages} messages"
                )

    def _update_twitch_api(self, twitch_api: Any) -> None:
        if not twitch_api:
            self.twitch_display = "Twitch not started"
            self.viewer_delta_label = ""
            return
        if time.time() - self.last_twitch_poll < self.settings.twitch_analytics_seconds:
            return
        self.last_twitch_poll = time.time()
        previous_viewers = None if self.latest_twitch is None else self.latest_twitch.viewer_count
        self.latest_twitch = twitch_api.snapshot(self.logger.stream_time())
        self.logger.add_twitch_snapshot(twitch_api.to_dict(self.latest_twitch))
        if self.latest_twitch.connected:
            self.twitch_display = (
                f"{'LIVE' if self.latest_twitch.live else 'Offline'}\n"
                f"Viewers: {self.latest_twitch.viewer_count}\n"
                f"Game: {self.latest_twitch.game_name or '?'}\n"
                f"Followers: {self.latest_twitch.follower_total if self.latest_twitch.follower_total is not None else '?'}"
            )
            if previous_viewers is not None:
                delta = self.latest_twitch.viewer_count - previous_viewers
                self.viewer_delta = delta
                if delta >= 2:
                    self.viewer_delta_label = (
                        f"📈 Viewer spike: +{delta}, now {self.latest_twitch.viewer_count}"
                    )
                elif delta <= -2:
                    self.viewer_delta_label = (
                        f"📉 Viewer drop: {delta}, now {self.latest_twitch.viewer_count}"
                    )
                else:
                    self.viewer_delta_label = ""
                if self.viewer_delta_label:
                    self.moment_updates.append(self.viewer_delta_label)
            else:
                self.viewer_delta = 0
                self.viewer_delta_label = ""
        else:
            self.twitch_display = f"API Error\n{self.latest_twitch.error}"
            self.viewer_delta = 0
            self.viewer_delta_label = ""

    def _update_eventsub(self, eventsub: Any) -> None:
        if not eventsub:
            return
        events = eventsub.drain()
        if not events:
            return
        event_dicts = [eventsub.to_dict(event) for event in events]
        self.logger.add_twitch_events(event_dicts)
        self.event_updates = events
        self.ai_timeline_updates = [
            f"[{datetime.fromtimestamp(event.timestamp_epoch).strftime('%H:%M:%S')}] Twitch Event\n{event.message}\n"
            for event in events
        ]

    def _update_live_status(self) -> None:
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
        self.live_status = (
            f"{obs_line}\n"
            f"{twitch_line}\n"
            f"Avg viewers: {viewers.get('average_viewers', 0)} | "
            f"Peak: {viewers.get('peak_viewers', 0)}\n"
            f"Human chat: {summary.get('total_chat_messages', 0)} | "
            f"Unique chatters: {summary.get('unique_chatters', 0)} | "
            f"Bot filtered: {summary.get('bot_chat_messages', 0)}\n"
            f"{top_viewer_line}"
        )

    def _update_analytics(self, ai: Any) -> dict[str, Any]:
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
        self.analytics_text = "\n".join(lines)
        self.summary = summary
        self.ai_notes = self._build_ai_notes(ai)
        return {
            "summary": summary,
            "analytics_text": self.analytics_text,
            "ai_notes": self.ai_notes,
        }

    def _build_ai_notes(self, ai: Any) -> str:
        if time.time() - self.last_ai_refresh < self.settings.ai_refresh_seconds:
            return self.ai_notes_text if hasattr(self, "ai_notes_text") else ""
        self.last_ai_refresh = time.time()
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
        notes = ai.suggest(
            self.latest_obs,
            self.recent_chat,
            self.latest_twitch,
            recent_events=recent_events,
            recent_highlights=recent_highlights,
            chat_history=self.logger.chat_history,
            viewer_memory=self.logger.viewer_memory,
        )
        self.ai_notes_text = notes
        if self._should_post_ai_timeline(notes):
            self.last_ai_notes_text = notes.strip()
            self.last_ai_timeline_post = time.time()
        return notes

    def _should_post_ai_timeline(self, notes: str) -> bool:
        clean_notes = notes.strip()
        if not clean_notes:
            return False
        if clean_notes != self.last_ai_notes_text:
            return True
        if time.time() - self.last_ai_timeline_post >= self.ai_force_repeat_seconds:
            return True
        return False

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return "?"
        return f"{value:.2f}" if isinstance(value, float) else str(value)
