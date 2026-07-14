from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SecretStore:
    """Small abstraction for persisting sensitive runtime data.

    The default implementation stores values on disk, but the interface allows
    future swap-ins for OS credential stores without changing the application
    flow.
    """

    def load(self) -> dict[str, Any] | None:
        raise NotImplementedError

    def save(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError


class FileSecretStore(SecretStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
