from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_deep_analytics_report(
    report_path: str | Path, session_id: str | None = None
) -> dict[str, Any]:
    path = Path(report_path)
    text = path.read_text(encoding="utf-8", errors="replace")

    return {
        "title": "Stream Complete",
        "session_id": session_id or path.stem,
        "duration": _match(text, r"Stream length tracked:\s*(.+)"),
        "stream_score": _match(text, r"- Overall:\s*(.+)"),
        "category": _match(text, r"- Category:\s*(.+)"),
        "average_viewers": _match(text, r"- Average viewers:\s*(.+)"),
        "peak_viewers": _match(text, r"- Peak viewers:\s*(.+)"),
        "human_messages": _match(text, r"- Human chat messages:\s*(.+)"),
        "unique_chatters": _match(text, r"- Unique human chatters:\s*(.+)"),
        "highlights": _extract_highlights(text),
        "tips": _extract_tips(text),
    }


def _match(text: str, pattern: str, default: str = "Unknown") -> str:
    found = re.search(pattern, text, re.MULTILINE)
    return found.group(1).strip() if found else default


def _extract_highlights(text: str) -> list[str]:
    lines = []
    for match in re.finditer(r"###\s+(.+?)\n-\s+Reason:\s+(.+)", text):
        timestamp = match.group(1).strip()
        reason = match.group(2).strip()
        lines.append(f"{timestamp}: {reason}")
    return lines[:5]


def _extract_tips(text: str) -> list[str]:
    marker = "## Next Stream Tips"
    if marker not in text:
        return []

    section = text.split(marker, 1)[1]
    tips = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            tips.append(line[2:].strip())
    return tips[:5]
