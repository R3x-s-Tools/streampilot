from __future__ import annotations

import json
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp_epoch": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra = getattr(record, "extra_payload", None)
        if isinstance(extra, dict):
            payload.update(extra)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.handlers:
        return

    human_handler = RotatingFileHandler(
        LOG_DIR / "command_center.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    human_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    json_handler = RotatingFileHandler(
        LOG_DIR / "command_center.jsonl",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    json_handler.setFormatter(JsonLineFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))

    root_logger.addHandler(human_handler)
    root_logger.addHandler(json_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, message: str, **payload: Any) -> None:
    logger.log(level, message, extra={"extra_payload": payload})
