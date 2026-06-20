# v0.2.0 Patch: AI Producer 2.0, Viewer Memory, Better Logging

## Add files

Copy these into your repo:

```text
core/app_logger.py
analytics/viewer_memory.py
analytics/conversation_engine.py
ai/producer_v2.py
tests/test_viewer_memory.py
tests/test_conversation_engine.py
```

## Patch analytics/logger.py

Add imports:

```python
from core.app_logger import get_logger, log_event
from analytics.viewer_memory import ViewerMemory
```

In `__init__`, add:

```python
self.app_log = get_logger("analytics.stream_logger")
self.viewer_memory = ViewerMemory()
```

In `add_chat`, after appending each message, add:

```python
memory_result = self.viewer_memory.observe_chat(msg.username, msg.message, msg.timestamp)

if not memory_result.get("ignored"):
    log_event(
        self.app_log,
        20,
        "chat_observed",
        username=msg.username,
        stream_time=self.stream_time(msg.timestamp),
        viewer_memory=memory_result,
    )
```

In `add_twitch_events`, inside the loop, add:

```python
display_name = e.get("display_name") or e.get("username") or e.get("user_name")
memory_result = self.viewer_memory.observe_twitch_event(
    display_name or "unknown",
    e.get("event_type", "twitch_event"),
    e.get("timestamp_epoch"),
)

log_event(
    self.app_log,
    20,
    "twitch_event_observed",
    event_type=e.get("event_type"),
    display_name=display_name,
    viewer_memory=memory_result,
)
```

In `summary()`, add:

```python
"top_viewers": self.viewer_memory.top_viewers(10),
```

## Patch ui/main_window.py

Replace:

```python
from ai.producer import AiProducer
```

with:

```python
from ai.producer_v2 import AiProducerV2
```

Replace `self.ai = AiProducer(...)` with:

```python
self.ai = AiProducerV2(
    self.settings.ai_provider,
    self.settings.openai_api_key,
    self.settings.openai_model,
)
```

Replace `_ai_notes()` with:

```python
def _ai_notes(self):
    recent_events = self.logger.twitch_events[-10:]
    recent_highlights = [
        {
            "stream_time": e.stream_time,
            "event_type": e.event_type,
            "score": e.score,
            "reason": e.reason,
        }
        for e in self.logger.events[-10:]
    ]

    notes = self.ai.suggest(
        self.latest_obs,
        self.recent_chat,
        self.latest_twitch,
        recent_events=recent_events,
        recent_highlights=recent_highlights,
        chat_history=self.logger.chat_history,
        viewer_memory=self.logger.viewer_memory,
    )

    self.ai_box.setPlainText(notes)
```

## Update .gitignore

Add:

```gitignore
logs/
data/viewer_memory.json
```

Viewer memory can contain usernames/topics, so keep it private.

## Branch commands

```bash
git checkout develop
git pull
git checkout -b feature/ai-producer-v2-viewer-memory
```

After copying and patching:

```bash
git add .
git commit -m "Add AI Producer v2 viewer memory and structured logging"
git push -u origin feature/ai-producer-v2-viewer-memory
```

Open PR:

```text
feature/ai-producer-v2-viewer-memory -> develop
```
