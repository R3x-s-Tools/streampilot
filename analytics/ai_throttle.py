from __future__ import annotations

import time


class AiTimelineThrottle:
    """
    Decides when AI Producer notes should be added to the timeline.

    The live "What to do next" box can update often, but the timeline should not
    repeat the same advice over and over unless enough time has passed.
    """

    def __init__(self, force_repeat_seconds: int = 600):
        self.last_notes_text = ""
        self.last_post_epoch = 0.0
        self.force_repeat_seconds = force_repeat_seconds

    def should_post(self, notes: str, auto: bool = False, now_epoch: float | None = None) -> bool:
        clean_notes = (notes or "").strip()

        if not clean_notes:
            return False

        if not auto:
            return True

        if clean_notes != self.last_notes_text:
            return True

        now = now_epoch if now_epoch is not None else time.time()

        return now - self.last_post_epoch >= self.force_repeat_seconds

    def mark_posted(self, notes: str, now_epoch: float | None = None) -> None:
        self.last_notes_text = (notes or "").strip()
        self.last_post_epoch = now_epoch if now_epoch is not None else time.time()
