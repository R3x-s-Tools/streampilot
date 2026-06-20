from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from analytics.bot_filter import is_bot


@dataclass
class ViewerProfile:
    username: str
    first_seen_epoch: float
    last_seen_epoch: float
    streams_seen: int = 0
    total_messages: int = 0
    total_twitch_events: int = 0
    topics: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def is_regular(self) -> bool:
        return self.streams_seen >= 3 or self.total_messages >= 25

    @property
    def engagement_score(self) -> int:
        return int(
            min(
                100,
                self.total_messages * 2 + self.streams_seen * 12 + self.total_twitch_events * 15,
            )
        )


class ViewerMemory:
    def __init__(self, path: str = "data/viewer_memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)
        self.profiles: dict[str, ViewerProfile] = {}
        self._seen_this_session: set[str] = set()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.profiles = {
                username: ViewerProfile(**profile)
                for username, profile in raw.get("profiles", {}).items()
            }
        except Exception:
            self.profiles = {}

    def save(self) -> None:
        payload = {
            "profiles": {
                username: asdict(profile) for username, profile in sorted(self.profiles.items())
            }
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def observe_chat(
        self, username: str, message: str, timestamp_epoch: float | None = None
    ) -> dict:
        username_key = (username or "").strip().lower()
        if not username_key or is_bot(username_key):
            return {"ignored": True, "reason": "bot_or_empty"}

        now = timestamp_epoch or time.time()
        is_new_viewer = username_key not in self.profiles
        profile = self.profiles.get(username_key)

        if not profile:
            profile = ViewerProfile(
                username=username_key, first_seen_epoch=now, last_seen_epoch=now
            )
            self.profiles[username_key] = profile

        first_message_this_session = username_key not in self._seen_this_session
        if first_message_this_session:
            profile.streams_seen += 1
            self._seen_this_session.add(username_key)

        profile.last_seen_epoch = now
        profile.total_messages += 1
        self._update_topics(profile, message)
        self.save()

        return {
            "ignored": False,
            "username": username_key,
            "is_new_viewer": is_new_viewer,
            "first_message_this_session": first_message_this_session,
            "is_regular": profile.is_regular,
            "engagement_score": profile.engagement_score,
            "streams_seen": profile.streams_seen,
            "total_messages": profile.total_messages,
            "topics": profile.topics[-8:],
        }

    def observe_twitch_event(
        self, username: str, event_type: str, timestamp_epoch: float | None = None
    ) -> dict:
        username_key = (username or "").strip().lower()
        if not username_key or username_key == "unknown" or is_bot(username_key):
            return {"ignored": True, "reason": "bot_or_empty"}

        now = timestamp_epoch or time.time()
        profile = self.profiles.get(username_key)
        is_new_viewer = profile is None

        if not profile:
            profile = ViewerProfile(
                username=username_key, first_seen_epoch=now, last_seen_epoch=now
            )
            self.profiles[username_key] = profile

        if username_key not in self._seen_this_session:
            profile.streams_seen += 1
            self._seen_this_session.add(username_key)

        profile.last_seen_epoch = now
        profile.total_twitch_events += 1
        profile.notes.append(f"{event_type} at {int(now)}")
        profile.notes = profile.notes[-20:]
        self.save()

        return {
            "ignored": False,
            "username": username_key,
            "is_new_viewer": is_new_viewer,
            "is_regular": profile.is_regular,
            "engagement_score": profile.engagement_score,
            "streams_seen": profile.streams_seen,
            "total_messages": profile.total_messages,
            "total_twitch_events": profile.total_twitch_events,
        }

    def top_viewers(self, limit: int = 10) -> list[dict]:
        profiles = sorted(
            self.profiles.values(),
            key=lambda p: (p.engagement_score, p.last_seen_epoch),
            reverse=True,
        )
        return [
            asdict(profile)
            | {
                "engagement_score": profile.engagement_score,
                "is_regular": profile.is_regular,
            }
            for profile in profiles[:limit]
        ]

    def _update_topics(self, profile: ViewerProfile, message: str) -> None:
        text = (message or "").lower()
        topics = {
            "squad": ["squad", "fob", "map", "match", "kills", "faction"],
            "gta_rp": ["gta", "fivem", "rp", "redm", "outkast", "bernie"],
            "star_citizen": ["star citizen"],
            "finland": ["finland", "finnish", "midsummer", "juhannus"],
            "stream_support": ["follow", "lurking", "lurk", "watching"],
        }

        for topic, keywords in topics.items():
            if any(keyword in text for keyword in keywords) and topic not in profile.topics:
                profile.topics.append(topic)

        profile.topics = profile.topics[-20:]
