from __future__ import annotations

DEFAULT_BOT_NAMES = {
    "streamelements",
    "streamlabs",
    "nightbot",
    "wizebot",
    "moobot",
    "fossabot",
    "botrix",
    "own3d",
    "soundalerts",
    "blerp",
    "tangiabot",
    "tangia",
    "stream_pops",
    "commanderroot",
    "sery_bot",
    "dad_r3x",
}


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def is_bot(username: str, extra_bots: set[str] | None = None) -> bool:
    name = normalize_username(username)
    bots = set(DEFAULT_BOT_NAMES)

    if extra_bots:
        bots.update(normalize_username(bot) for bot in extra_bots)

    return name in bots


def filter_human_chat(
    chat_history: list[dict],
    extra_bots: set[str] | None = None,
) -> list[dict]:
    return [
        message
        for message in chat_history
        if not is_bot(str(message.get("username", "")), extra_bots)
    ]
