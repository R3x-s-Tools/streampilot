from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from analytics.bot_filter import is_bot


@dataclass
class MomentContext:
    stream_time: str
    event_type: str
    score: int
    reason: str
    likely_cause: str
    human_chat_nearby: list[dict]
    bot_chat_nearby: list[dict]
    twitch_events_nearby: list[dict]
    viewer_details: dict


class AnalyticsEngine:
    def __init__(self, chat_window_seconds: int = 180):
        self.chat_window_seconds = chat_window_seconds

    def build_contextual_moments(
        self,
        events: list[Any],
        chat_history: list[dict],
        twitch_events: list[dict],
    ) -> list[dict]:
        moments: list[MomentContext] = []

        for event in events:
            event_dict = self._event_to_dict(event)
            event_ts = float(event_dict.get("timestamp_epoch", 0) or 0)
            event_type = event_dict.get("event_type", "")
            details = event_dict.get("details", {}) or {}

            nearby_chat = self._nearby(chat_history, event_ts)
            human_chat = [item for item in nearby_chat if not is_bot(str(item.get("username", "")))]
            bot_chat = [item for item in nearby_chat if is_bot(str(item.get("username", "")))]
            nearby_events = self._nearby(twitch_events, event_ts)

            moments.append(
                MomentContext(
                    stream_time=event_dict.get("stream_time", "?"),
                    event_type=event_type,
                    score=self._clip_score(event_dict, human_chat, nearby_events),
                    reason=event_dict.get("reason", ""),
                    likely_cause=self._likely_cause(
                        event_type,
                        human_chat,
                        bot_chat,
                        nearby_events,
                    ),
                    human_chat_nearby=human_chat[-8:],
                    bot_chat_nearby=bot_chat[-5:],
                    twitch_events_nearby=nearby_events[-5:],
                    viewer_details=details,
                )
            )

        moments.sort(key=lambda item: item.score, reverse=True)
        return [asdict(moment) for moment in moments]

    def stream_score(self, summary: dict) -> dict:
        viewers = summary.get("viewer_summary", {})
        peak = float(viewers.get("peak_viewers", 0) or 0)
        average = float(viewers.get("average_viewers", 0) or 0)
        human_messages = int(summary.get("total_chat_messages", 0) or 0)
        unique_chatters = int(summary.get("unique_chatters", 0) or 0)
        moments = summary.get("contextual_moments", [])

        viewer_score = min(100, int((average * 12) + (peak * 4)))
        chat_score = min(100, int((human_messages * 1.5) + (unique_chatters * 10)))
        clip_score = min(
            100,
            int(max([moment.get("score", 0) for moment in moments], default=0) * 10),
        )
        technical_score = 100

        overall = int(
            viewer_score * 0.30 + chat_score * 0.25 + clip_score * 0.25 + technical_score * 0.20
        )

        return {
            "overall": overall,
            "viewer_retention": viewer_score,
            "chat_engagement": chat_score,
            "clip_potential": clip_score,
            "technical": technical_score,
        }

    def _event_to_dict(self, event: Any) -> dict:
        if isinstance(event, dict):
            return event

        return {
            "timestamp_epoch": getattr(event, "timestamp_epoch", 0),
            "stream_time": getattr(event, "stream_time", "?"),
            "event_type": getattr(event, "event_type", ""),
            "score": getattr(event, "score", 0),
            "reason": getattr(event, "reason", ""),
            "details": getattr(event, "details", {}),
        }

    def _nearby(self, items: list[dict], timestamp_epoch: float) -> list[dict]:
        if not timestamp_epoch:
            return []

        return [
            item
            for item in items
            if abs(float(item.get("timestamp_epoch", 0) or 0) - timestamp_epoch)
            <= self.chat_window_seconds
        ]

    def _likely_cause(
        self,
        event_type: str,
        human_chat: list[dict],
        bot_chat: list[dict],
        twitch_events: list[dict],
    ) -> str:
        text = " ".join(
            [str(item.get("message", "")) for item in human_chat + bot_chat]
            + [str(item.get("message", "")) for item in twitch_events]
        ).lower()

        if "raid" in text or "inbound" in text:
            return "Likely community support, raid, shoutout, or another streamer sending viewers."

        if "follow" in text:
            return "Likely new follower or community interaction moment."

        if "cheer" in text or "bits" in text:
            return "Likely bits/cheer engagement moment."

        if len(human_chat) >= 5:
            return "Likely human chat activity spike."

        if event_type == "viewer_spike":
            return (
                "Viewer spike detected, but nearby context was limited. Review this VOD timestamp."
            )

        if event_type == "viewer_drop":
            return "Viewer drop detected. Check for downtime, menus, silence, round transition, or stream ending."

        return "General stream event."

    def _clip_score(
        self,
        event_dict: dict,
        human_chat: list[dict],
        twitch_events: list[dict],
    ) -> int:
        score = int(event_dict.get("score", 5) or 5)
        event_type = event_dict.get("event_type", "")
        details = event_dict.get("details", {}) or {}

        if event_type == "viewer_spike":
            score += min(4, max(1, int(details.get("delta", 0) or 0)))

        if event_type == "manual_clip_marker":
            score += 5

        if len(human_chat) >= 5:
            score += 3
        elif len(human_chat) >= 2:
            score += 1

        event_text = " ".join(str(event.get("message", "")) for event in twitch_events).lower()

        if "raid" in event_text:
            score += 5

        if "follow" in event_text:
            score += 2

        if "cheer" in event_text or "bits" in event_text:
            score += 4

        if "subscription" in event_text or "sub" in event_text:
            score += 4

        if event_type == "viewer_drop":
            score = min(score, 6)

        return max(1, min(10, score))
