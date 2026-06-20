from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass

from analytics.bot_filter import is_bot


@dataclass
class ConversationSignal:
    username: str
    messages_10m: int
    messages_30m: int
    question_count: int
    is_high_engagement: bool
    suggested_prompt: str


class ConversationEngine:
    def analyze_recent_chat(self, chat_history: list[dict], now_epoch: float) -> list[dict]:
        human_chat = [msg for msg in chat_history if not is_bot(str(msg.get("username", "")))]

        by_user_10m: dict[str, list[dict]] = defaultdict(list)
        by_user_30m: dict[str, list[dict]] = defaultdict(list)

        for msg in human_chat:
            ts = float(msg.get("timestamp_epoch", 0) or 0)
            username = str(msg.get("username", "")).lower()

            if now_epoch - ts <= 600:
                by_user_10m[username].append(msg)
            if now_epoch - ts <= 1800:
                by_user_30m[username].append(msg)

        signals: list[ConversationSignal] = []

        for username, messages_30 in by_user_30m.items():
            messages_10 = by_user_10m.get(username, [])
            question_count = sum(1 for msg in messages_30 if "?" in str(msg.get("message", "")))
            is_high = len(messages_10) >= 4 or len(messages_30) >= 8 or question_count >= 2

            if not is_high:
                continue

            signals.append(
                ConversationSignal(
                    username=username,
                    messages_10m=len(messages_10),
                    messages_30m=len(messages_30),
                    question_count=question_count,
                    is_high_engagement=is_high,
                    suggested_prompt=self._suggest_prompt(username, messages_30),
                )
            )

        signals.sort(key=lambda s: (s.messages_10m, s.messages_30m, s.question_count), reverse=True)
        return [asdict(signal) for signal in signals]

    def _suggest_prompt(self, username: str, messages: list[dict]) -> str:
        text = " ".join(str(msg.get("message", "")).lower() for msg in messages[-8:])

        if "finland" in text or "finnish" in text or "midsummer" in text:
            return f"Ask {username} what Squad servers or maps are popular in Finland."
        if "squad" in text or "fob" in text or "map" in text:
            return f"Ask {username} what role or kit they usually play in Squad."
        if "gta" in text or "fivem" in text or "redm" in text:
            return f"Ask {username} about their favorite RP character or server memory."
        if "star citizen" in text:
            return f"Ask {username} what ship or loop they are running in Star Citizen."

        return f"Ask {username} a direct follow-up based on their last message."
