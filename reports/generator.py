from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json


class ReportGenerator:
    def __init__(self, ai_provider="off", openai_api_key="", model="gpt-4.1-mini"):
        self.ai_provider = ai_provider
        self.openai_api_key = openai_api_key
        self.model = model
        Path("stream_reports").mkdir(exist_ok=True)

    def generate(self, payload):
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        highlight = Path("stream_reports") / f"highlight_report_{stamp}.md"
        analytics = Path("stream_reports") / f"deep_analytics_report_{stamp}.md"
        highlight.write_text(self._highlight(payload), encoding="utf-8")
        analytics.write_text(self._analytics(payload), encoding="utf-8")
        return highlight, analytics

    def _highlight(self, p):
        vs = p.get("viewer_summary", {})
        moments = p.get("contextual_moments", []) or p.get("top_events", [])
        lines = [
            "# Dad_R3x Highlight Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Stream length tracked: {p.get('stream_length')}",
            "",
            "## Viewer Snapshot",
            "",
            f"- Average viewers: {vs.get('average_viewers', 0)}",
            f"- Peak viewers: {vs.get('peak_viewers', 0)}",
            f"- Low viewers: {vs.get('low_viewers', 0)}",
            "",
            "## Best Clip Candidates",
            "",
        ]
        if not moments:
            lines.append("No clip candidates detected yet.")
        for i, m in enumerate(moments[:15], 1):
            lines += [
                f"### {i}. {m.get('stream_time', '?')} - Clip Confidence {m.get('score', '?')}/10",
                f"- Type: {m.get('event_type', '')}",
                f"- Reason: {m.get('reason', '')}",
                f"- Likely cause: {m.get('likely_cause', 'Unknown')}",
                "",
            ]
            nearby = m.get("human_chat_nearby", [])
            if nearby:
                lines.append("Nearby human chat:")
                for msg in nearby[-5:]:
                    lines.append(f"- {msg.get('username')}: {msg.get('message')}")
                lines.append("")
        return "\n".join(lines)

    def _analytics(self, p):
        if self.ai_provider == "openai" and self.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.openai_api_key)
                prompt = f"""Create a practical post-stream analytics report for Dad_R3x in Markdown.

Include:
1. Executive summary
2. Stream score breakdown
3. Viewer performance
4. Human chat engagement, excluding bots
5. Best moments with likely causes
6. Viewer drops and possible reasons
7. Next-stream tactical improvements
8. 3 short-form clip ideas

Data:
{json.dumps(p, indent=2)}
"""
                return client.responses.create(model=self.model, input=prompt).output_text
            except Exception as exc:
                return self._rules(p) + f"\n\nAI report error: {exc}\n"
        return self._rules(p)

    def _rules(self, p):
        vs = p.get("viewer_summary", {})
        latest = p.get("latest_twitch", {})
        score = p.get("stream_score", {})
        moments = p.get("contextual_moments", [])
        lines = [
            "# Dad_R3x Deep Stream Analytics Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Stream length tracked: {p.get('stream_length')}",
            "",
            "## Stream Score",
            "",
            f"- Overall: {score.get('overall', '?')}/100",
            f"- Viewer retention: {score.get('viewer_retention', '?')}/100",
            f"- Chat engagement: {score.get('chat_engagement', '?')}/100",
            f"- Clip potential: {score.get('clip_potential', '?')}/100",
            f"- Technical: {score.get('technical', '?')}/100",
            "",
            "## Stream Info",
            "",
            f"- Live status: {latest.get('live', 'unknown')}",
            f"- Title: {latest.get('title', '')}",
            f"- Category: {latest.get('game_name', '')}",
            "",
            "## Viewer Summary",
            "",
            f"- Average viewers: {vs.get('average_viewers', 0)}",
            f"- Peak viewers: {vs.get('peak_viewers', 0)}",
            f"- Low viewers: {vs.get('low_viewers', 0)}",
            f"- Viewer samples: {vs.get('samples', 0)}",
            "",
            "## Human Engagement",
            "",
            f"- Human chat messages: {p.get('total_chat_messages', 0)}",
            f"- Unique human chatters: {p.get('unique_chatters', 0)}",
            f"- Bot/system messages filtered: {p.get('bot_chat_messages', 0)}",
            f"- Twitch events captured: {len(p.get('recent_twitch_events', []))}",
            "",
            "## Best Contextual Moments",
            "",
        ]
        if not moments:
            lines.append("No contextual moments detected yet.")
        else:
            for m in moments[:8]:
                lines += [
                    f"### {m.get('stream_time', '?')} - {m.get('event_type', '')} - {m.get('score', '?')}/10",
                    f"- Reason: {m.get('reason', '')}",
                    f"- Likely cause: {m.get('likely_cause', '')}",
                    "",
                ]
        lines += [
            "## Next Stream Tips",
            "",
            "- Use manual clip markers during obvious Squad firefights, raids, funny comms, and clutch moments.",
            "- Ask one direct question every 10-15 minutes during downtime.",
            "- Review the highest confidence clip moments first.",
            "- Watch viewer drops and compare them against menus, downtime, round transitions, or low commentary.",
            "- Turn the top timestamp into one short-form clip within 24 hours.",
        ]
        return "\n".join(lines)
