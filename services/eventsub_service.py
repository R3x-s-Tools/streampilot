from __future__ import annotations

import json, queue, threading, time
from dataclasses import dataclass, asdict
from typing import Callable, Optional
import requests
import websocket


@dataclass
class TwitchEvent:
    timestamp_epoch: float
    event_type: str
    display_name: str
    message: str
    raw: dict


class EventSubService:
    WS_URL = "wss://eventsub.wss.twitch.tv/ws"
    HELIX = "https://api.twitch.tv/helix"

    def __init__(self, client_id: str, channel: str, token_provider: Callable[[], Optional[str]]):
        self.client_id = client_id
        self.channel = channel.lower().strip().lstrip("#")
        self.token_provider = token_provider
        self.events: queue.Queue[TwitchEvent] = queue.Queue()
        self.running = False
        self.ws = None
        self.status = "Stopped"
        self.last_error = ""
        self.session_id = ""
        self.broadcaster_id = ""
        self.user_id = ""
        self.subscribed = []

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass

    def drain(self):
        out = []
        while not self.events.empty():
            out.append(self.events.get())
        return out

    def _headers(self):
        token = self.token_provider()
        if not token:
            raise RuntimeError("No Twitch access token. Login first.")
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint, params=None):
        resp = requests.get(
            f"{self.HELIX}/{endpoint}", headers=self._headers(), params=params or {}, timeout=10
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"GET {endpoint} {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def _post(self, endpoint, payload):
        resp = requests.post(
            f"{self.HELIX}/{endpoint}", headers=self._headers(), json=payload, timeout=10
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"POST {endpoint} {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def _lookup_ids(self):
        data = self._get("users", {"login": self.channel}).get("data", [])
        if not data:
            raise RuntimeError(f"Channel not found: {self.channel}")
        self.broadcaster_id = data[0]["id"]
        me = self._get("users").get("data", [])
        if not me:
            raise RuntimeError("Could not identify token user.")
        self.user_id = me[0]["id"]

    def _run(self):
        while self.running:
            try:
                self.status = "Looking up IDs..."
                self._lookup_ids()
                self.status = "Connecting..."
                self.ws = websocket.WebSocketApp(
                    self.WS_URL,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as exc:
                self.last_error = str(exc)
                self.status = f"Error: {exc}"
                print(f"[EventSub ERROR] {exc}")
            if self.running:
                time.sleep(5)

    def _on_error(self, ws, error):
        self.last_error = str(error)
        self.status = f"Error: {error}"

    def _on_close(self, ws, code, msg):
        self.status = f"Closed: {code} {msg}"

    def _on_message(self, ws, message):
        try:
            payload = json.loads(message)
            mt = payload.get("metadata", {}).get("message_type")
            if mt == "session_welcome":
                self.session_id = payload["payload"]["session"]["id"]
                self._subscribe_all()
            elif mt == "notification":
                sub_type = payload["payload"]["subscription"]["type"]
                event = payload["payload"]["event"]
                self.events.put(self._parse(sub_type, event, payload))
            elif mt == "session_reconnect":
                ws.close()
        except Exception as exc:
            self.last_error = str(exc)

    def _subscribe_all(self):
        subs = [
            (
                "channel.follow",
                "2",
                {"broadcaster_user_id": self.broadcaster_id, "moderator_user_id": self.user_id},
            ),
            ("channel.subscribe", "1", {"broadcaster_user_id": self.broadcaster_id}),
            ("channel.subscription.message", "1", {"broadcaster_user_id": self.broadcaster_id}),
            ("channel.subscription.gift", "1", {"broadcaster_user_id": self.broadcaster_id}),
            ("channel.cheer", "1", {"broadcaster_user_id": self.broadcaster_id}),
            ("channel.raid", "1", {"to_broadcaster_user_id": self.broadcaster_id}),
            (
                "channel.channel_points_custom_reward_redemption.add",
                "1",
                {"broadcaster_user_id": self.broadcaster_id},
            ),
        ]
        self.subscribed = []
        for typ, ver, cond in subs:
            try:
                self._post(
                    "eventsub/subscriptions",
                    {
                        "type": typ,
                        "version": ver,
                        "condition": cond,
                        "transport": {"method": "websocket", "session_id": self.session_id},
                    },
                )
                self.subscribed.append(typ)
            except Exception as exc:
                print(f"[EventSub subscribe skipped] {typ}: {exc}")
        self.status = f"Active: {len(self.subscribed)} subscriptions"

    def _parse(self, typ, event, raw):
        name = event.get("user_name") or event.get("from_broadcaster_user_name") or "Unknown"
        if typ == "channel.follow":
            msg = f"{name} followed."
        elif typ == "channel.cheer":
            msg = f"{name} cheered {event.get('bits', 0)} bits. {event.get('message', '')}"
        elif typ == "channel.raid":
            msg = f"{event.get('from_broadcaster_user_name', name)} raided with {event.get('viewers', 0)} viewers."
        elif "subscription.gift" in typ:
            msg = f"{name} gifted {event.get('total', 1)} sub(s)."
        elif "subscription.message" in typ:
            msg = f"{name} resubbed. {((event.get('message') or {}).get('text') or '')}"
        elif "subscribe" in typ:
            msg = f"{name} subscribed."
        elif "redemption" in typ:
            msg = f"{name} redeemed {event.get('reward', {}).get('title', 'a reward')}."
        else:
            msg = f"{typ}: {name}"
        return TwitchEvent(time.time(), typ, name, msg.strip(), raw)

    @staticmethod
    def to_dict(event):
        return asdict(event)
