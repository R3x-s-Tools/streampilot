from __future__ import annotations

from datetime import datetime


def generate_session_id(prefix: str = "stream") -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{stamp}"
