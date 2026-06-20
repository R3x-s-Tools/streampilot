from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Callable, Optional
import requests


@dataclass
class TwitchSnapshot:
    timestamp_epoch: float
    stream_time: str
    connected: bool = False
    live: bool = False
    broadcaster_id: str = ""
    channel_login: str = ""
    title: str = ""
    game_name: str = ""
    viewer_count: int = 0
    started_at: str = ""
    follower_total: int | None = None
    subscriber_total: int | None = None
    error: str = ""


class TwitchApiService:
    def __init__(
        self, client_id: str, channel: str, access_token_provider: Callable[[], Optional[str]]
    ):
        self.client_id = client_id
        self.channel = channel.lower().strip().lstrip("#")
        self.access_token_provider = access_token_provider
        self.broadcaster_id = ""
        self.status = "Stopped"
        self.last_error = ""

    def _headers(self):
        token = self.access_token_provider()
        if not token:
            raise RuntimeError("No Twitch access token. Login first.")
        return {"Client-ID": self.client_id, "Authorization": f"Bearer {token}"}

    def _get(self, endpoint: str, params: dict | None = None):
        resp = requests.get(
            f"https://api.twitch.tv/helix/{endpoint}",
            headers=self._headers(),
            params=params or {},
            timeout=10,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Twitch API {endpoint} failed {resp.status_code}: {resp.text[:300]}"
            )
        return resp.json()

    def _ensure_broadcaster_id(self):
        if self.broadcaster_id:
            return self.broadcaster_id
        data = self._get("users", {"login": self.channel}).get("data", [])
        if not data:
            raise RuntimeError(f"Channel not found: {self.channel}")
        self.broadcaster_id = data[0]["id"]
        return self.broadcaster_id

    def snapshot(self, stream_time: str) -> TwitchSnapshot:
        snap = TwitchSnapshot(time.time(), stream_time, channel_login=self.channel)
        try:
            bid = self._ensure_broadcaster_id()
            snap.broadcaster_id = bid
            snap.connected = True

            streams = self._get("streams", {"user_login": self.channel}).get("data", [])
            if streams:
                s = streams[0]
                snap.live = True
                snap.title = s.get("title", "")
                snap.game_name = s.get("game_name", "")
                snap.viewer_count = int(s.get("viewer_count", 0))
                snap.started_at = s.get("started_at", "")

            try:
                snap.follower_total = self._get(
                    "channels/followers", {"broadcaster_id": bid, "first": 1}
                ).get("total")
            except Exception as exc:
                snap.error = f"Follower total unavailable: {exc}"

            try:
                snap.subscriber_total = self._get(
                    "subscriptions", {"broadcaster_id": bid, "first": 1}
                ).get("total")
            except Exception:
                pass

            self.status = "Connected"
            return snap
        except Exception as exc:
            snap.error = str(exc)
            self.last_error = str(exc)
            self.status = f"Error: {exc}"
            return snap

    @staticmethod
    def to_dict(snap: TwitchSnapshot):
        return asdict(snap)
