from __future__ import annotations

import time
from typing import Any

from analytics.conversation_engine import ConversationEngine


class AiProducerV2:
    def __init__(self, provider: str = "off", api_key: str = "", model: str = "gpt-4.1-mini"):
        self.provider = (provider or "off").lower()
        self.api_key = api_key or ""
        self.model = model or "gpt-4.1-mini"
        self.conversation_engine = ConversationEngine()
        self.last_error = ""

    def suggest(
        self,
        obs: Any,
        recent_chat_objects: list[Any],
        twitch_snapshot: Any = None,
        recent_events: list[dict] | None = None,
        recent_highlights: list[dict] | None = None,
        chat_history: list[dict] | None = None,
        viewer_memory: Any = None,
    ) -> str:
        recent_events = recent_events or []
        recent_highlights = recent_highlights or []
        chat_history = chat_history or []

        conversation_signals = self.conversation_engine.analyze_recent_chat(
            chat_history, time.time()
        )
        top_viewers = viewer_memory.top_viewers(5) if viewer_memory else []

        if self.provider == "openai" and self.api_key:
            return self._openai_suggest(
                obs=obs,
                twitch_snapshot=twitch_snapshot,
                recent_events=recent_events,
                recent_highlights=recent_highlights,
                conversation_signals=conversation_signals,
                top_viewers=top_viewers,
            )

        return self._rules_only(
            obs=obs,
            twitch_snapshot=twitch_snapshot,
            recent_events=recent_events,
            recent_highlights=recent_highlights,
            conversation_signals=conversation_signals,
            top_viewers=top_viewers,
        )

    def _rules_only(
        self,
        obs: Any,
        twitch_snapshot: Any,
        recent_events: list[dict],
        recent_highlights: list[dict],
        conversation_signals: list[dict],
        top_viewers: list[dict],
    ) -> str:
        notes: list[str] = []

        if not getattr(obs, "connected", False):
            notes.append(f"OBS is disconnected: {getattr(obs, 'error', '')}")
        else:
            render_lag = getattr(obs, "render_lag_percent", None) or 0
            encoding_lag = getattr(obs, "encoding_lag_percent", None) or 0
            if render_lag >= 3 or encoding_lag >= 3:
                notes.append(
                    f"Technical warning: render lag {render_lag}%, encoding lag {encoding_lag}%. Reduce load before adding features."
                )
            else:
                notes.append("OBS is healthy. Focus on keeping the current conversation alive.")

        if conversation_signals:
            signal = conversation_signals[0]
            notes.append(
                f"{signal['username']} is highly engaged "
                f"({signal['messages_10m']} msgs/10m, {signal['messages_30m']} msgs/30m). "
                f"{signal['suggested_prompt']}"
            )
        else:
            notes.append(
                "No high-engagement conversation detected. Ask: “What kit should I run next round?”"
            )

        if top_viewers:
            regulars = [v for v in top_viewers if v.get("is_regular")]
            if regulars:
                notes.append(
                    f"Regular viewer active/history: {regulars[0]['username']} has {regulars[0]['total_messages']} lifetime messages."
                )
            else:
                notes.append(
                    f"Top viewer so far: {top_viewers[0]['username']} with engagement score {top_viewers[0]['engagement_score']}."
                )

        if twitch_snapshot and getattr(twitch_snapshot, "live", False):
            notes.append(
                f"Live in {getattr(twitch_snapshot, 'game_name', 'Unknown')} with "
                f"{getattr(twitch_snapshot, 'viewer_count', '?')} viewer(s)."
            )

        if recent_events:
            latest_event = recent_events[-1]
            notes.append(
                f"Recent Twitch event: {latest_event.get('message', latest_event.get('event_type', 'event'))}"
            )

        if recent_highlights:
            notes.append(
                "A highlight/viewer event was recently detected. Mark context manually if it was gameplay-related."
            )

        return "\n".join(f"🦖 {note}" for note in notes[:5])

    def _openai_suggest(
        self,
        obs: Any,
        twitch_snapshot: Any,
        recent_events: list[dict],
        recent_highlights: list[dict],
        conversation_signals: list[dict],
        top_viewers: list[dict],
    ) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            obs_context = {
                "connected": getattr(obs, "connected", False),
                "streaming": getattr(obs, "streaming", False),
                "scene": getattr(obs, "current_scene", "Unknown"),
                "fps": getattr(obs, "fps", None),
                "cpu_usage": getattr(obs, "cpu_usage", None),
                "render_lag_percent": getattr(obs, "render_lag_percent", None),
                "encoding_lag_percent": getattr(obs, "encoding_lag_percent", None),
                "error": getattr(obs, "error", ""),
            }

            twitch_context = None
            if twitch_snapshot:
                twitch_context = {
                    "live": getattr(twitch_snapshot, "live", False),
                    "viewer_count": getattr(twitch_snapshot, "viewer_count", None),
                    "title": getattr(twitch_snapshot, "title", ""),
                    "game_name": getattr(twitch_snapshot, "game_name", ""),
                }

            prompt = f"""
You are Dad_R3x's live AI producer.

Give max 5 short bullets. Each starts with 🦖.
Prioritize:
1. Technical emergency if present.
2. Keep strong viewer conversations alive.
3. Recognize regulars or likely future regulars.
4. Suggest exact questions Dad_R3x can ask.
5. Suggest clip markers only for useful moments.

Avoid generic advice.

OBS:
{obs_context}

Twitch:
{twitch_context}

Conversation signals:
{conversation_signals}

Top viewer memory:
{top_viewers}

Recent Twitch events:
{recent_events[-10:]}

Recent highlights:
{recent_highlights[-10:]}
"""
            response = client.responses.create(model=self.model, input=prompt)
            text = response.output_text.strip()
            self.last_error = ""
            return text or self._rules_only(
                obs,
                twitch_snapshot,
                recent_events,
                recent_highlights,
                conversation_signals,
                top_viewers,
            )

        except Exception as exc:
            self.last_error = str(exc)
            return (
                self._rules_only(
                    obs,
                    twitch_snapshot,
                    recent_events,
                    recent_highlights,
                    conversation_signals,
                    top_viewers,
                )
                + f"\n🦖 AI Producer error: {exc}"
            )
