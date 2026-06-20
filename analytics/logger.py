from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from analytics.bot_filter import filter_human_chat
from analytics.engine import AnalyticsEngine
from analytics.viewer_memory import ViewerMemory
from core.app_logger import get_logger, log_event


@dataclass
class StreamEvent:
    timestamp_epoch: float
    stream_time: str
    event_type: str
    score: int
    reason: str
    details: dict = field(default_factory=dict)


class StreamLogger:
    def __init__(self):
        self.started_at = time.time()

        Path("stream_logs").mkdir(exist_ok=True)

        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_file = Path("stream_logs") / f"stream_session_{stamp}.json"

        self.events: list[StreamEvent] = []
        self.chat_history: list[dict] = []
        self.obs_samples: list[dict] = []
        self.twitch_samples: list[dict] = []
        self.twitch_events: list[dict] = []

        self._last_viewers: Optional[int] = None
        self._last_viewer_event = 0

        self.analytics_engine = AnalyticsEngine()
        self.viewer_memory = ViewerMemory()
        self.app_log = get_logger("analytics.stream_logger")

        log_event(
            self.app_log,
            20,
            "stream_logger_started",
            session_file=str(self.session_file),
        )

    def stream_time(self, when: Optional[float] = None) -> str:
        seconds = int((when or time.time()) - self.started_at)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def add_event(
        self, event_type: str, score: int, reason: str, details: dict | None = None
    ) -> StreamEvent:
        event = StreamEvent(
            timestamp_epoch=time.time(),
            stream_time=self.stream_time(),
            event_type=event_type,
            score=max(1, min(10, int(score))),
            reason=reason,
            details=details or {},
        )

        self.events.append(event)

        log_event(
            self.app_log,
            20,
            "stream_event_added",
            event_type=event_type,
            score=event.score,
            reason=reason,
            stream_time=event.stream_time,
        )

        self.save()
        return event

    def add_chat(self, messages) -> None:
        for msg in messages:
            row = {
                "timestamp_epoch": msg.timestamp,
                "stream_time": self.stream_time(msg.timestamp),
                "username": msg.username,
                "message": msg.message,
            }
            self.chat_history.append(row)

            memory_result = self.viewer_memory.observe_chat(
                msg.username,
                msg.message,
                msg.timestamp,
            )

            if not memory_result.get("ignored"):
                log_event(
                    self.app_log,
                    20,
                    "chat_observed",
                    username=msg.username,
                    stream_time=row["stream_time"],
                    viewer_memory=memory_result,
                )

        self.chat_history = self.chat_history[-5000:]
        self.save()

    def add_obs(self, snap) -> None:
        sample = {
            "timestamp_epoch": time.time(),
            "stream_time": self.stream_time(),
            "connected": snap.connected,
            "streaming": snap.streaming,
            "recording": getattr(snap, "recording", False),
            "scene": snap.current_scene,
            "fps": snap.fps,
            "cpu_usage": snap.cpu_usage,
            "memory_usage_mb": snap.memory_usage_mb,
            "render_lag_percent": snap.render_lag_percent,
            "encoding_lag_percent": snap.encoding_lag_percent,
            "error": snap.error,
        }

        self.obs_samples.append(sample)
        self.obs_samples = self.obs_samples[-5000:]

        if not snap.connected:
            log_event(
                self.app_log,
                30,
                "obs_disconnected",
                error=snap.error,
                stream_time=sample["stream_time"],
            )

        self.save()

    def add_twitch_snapshot(self, sample: dict) -> None:
        self.twitch_samples.append(sample)
        self.twitch_samples = self.twitch_samples[-5000:]

        viewers = sample.get("viewer_count")

        if sample.get("live") and viewers is not None:
            viewers = int(viewers)

            if self._last_viewers is not None and time.time() - self._last_viewer_event > 60:
                delta = viewers - self._last_viewers
                details = dict(sample)
                details["delta"] = delta

                if delta >= 2:
                    self._last_viewer_event = time.time()
                    self.add_event(
                        "viewer_spike",
                        min(10, 6 + delta),
                        f"Viewer count increased by {delta}, now {viewers}.",
                        details,
                    )
                elif delta <= -2:
                    self._last_viewer_event = time.time()
                    self.add_event(
                        "viewer_drop",
                        5,
                        f"Viewer count dropped by {abs(delta)}, now {viewers}.",
                        details,
                    )

            self._last_viewers = viewers

        self.save()

    def add_twitch_events(self, event_dicts: list[dict]) -> None:
        for event in event_dicts:
            event["stream_time"] = self.stream_time(event.get("timestamp_epoch"))
            self.twitch_events.append(event)

            event_type = event.get("event_type", "")
            message = event.get("message", "Twitch event")

            display_name = (
                event.get("display_name")
                or event.get("username")
                or event.get("user_name")
                or "unknown"
            )

            memory_result = self.viewer_memory.observe_twitch_event(
                display_name,
                event_type or "twitch_event",
                event.get("timestamp_epoch"),
            )

            log_event(
                self.app_log,
                20,
                "twitch_event_observed",
                event_type=event_type,
                display_name=display_name,
                viewer_memory=memory_result,
            )

            score = 9 if any(x in event_type for x in ["subscription", "cheer", "raid"]) else 8
            self.add_event("twitch_event", score, message, event)

        self.twitch_events = self.twitch_events[-1000:]
        self.save()

    def manual_clip(self, scene: str) -> StreamEvent:
        return self.add_event(
            "manual_clip_marker",
            8,
            "Manual clip marker pressed.",
            {"scene": scene},
        )

    def save(self) -> None:
        payload = {
            "started_at": self.started_at,
            "started_at_readable": datetime.fromtimestamp(self.started_at).isoformat(),
            "events": [asdict(event) for event in self.events],
            "chat_history": self.chat_history[-5000:],
            "obs_samples": self.obs_samples[-5000:],
            "twitch_samples": self.twitch_samples[-5000:],
            "twitch_events": self.twitch_events[-1000:],
        }

        self.session_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def summary(self) -> dict:
        human_chat = filter_human_chat(self.chat_history)

        viewer_counts = [
            int(sample["viewer_count"])
            for sample in self.twitch_samples
            if sample.get("live") and sample.get("viewer_count") is not None
        ]

        contextual_moments = self.analytics_engine.build_contextual_moments(
            self.events,
            self.chat_history,
            self.twitch_events,
        )

        summary = {
            "stream_length": self.stream_time(),
            "total_chat_messages": len(human_chat),
            "unique_chatters": len(set(msg["username"] for msg in human_chat)),
            "bot_chat_messages": len(self.chat_history) - len(human_chat),
            "events": [asdict(event) for event in self.events],
            "top_events": [
                asdict(event)
                for event in sorted(self.events, key=lambda item: item.score, reverse=True)[:20]
            ],
            "contextual_moments": contextual_moments[:20],
            "viewer_summary": {
                "average_viewers": (
                    round(sum(viewer_counts) / len(viewer_counts), 2) if viewer_counts else 0
                ),
                "peak_viewers": max(viewer_counts) if viewer_counts else 0,
                "low_viewers": min(viewer_counts) if viewer_counts else 0,
                "samples": len(viewer_counts),
            },
            "recent_twitch_events": self.twitch_events[-100:],
            "latest_twitch": self.twitch_samples[-1] if self.twitch_samples else {},
            "human_chat_sample": human_chat[-100:],
            "top_viewers": self.viewer_memory.top_viewers(10),
        }

        summary["stream_score"] = self.analytics_engine.stream_score(summary)
        return summary
