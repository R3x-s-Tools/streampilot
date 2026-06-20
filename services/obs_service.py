from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ObsSnapshot:
    connected: bool = False
    streaming: bool = False
    recording: bool = False
    current_scene: str = "Unknown"
    fps: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    render_missed_frames: int = 0
    render_total_frames: int = 0
    render_lag_percent: Optional[float] = None
    output_skipped_frames: int = 0
    output_total_frames: int = 0
    encoding_lag_percent: Optional[float] = None
    error: str = ""


class ObsService:
    """
    OBS WebSocket service with connection cooldown.

    Why:
    If OBS is offline or the Windows PC is unreachable, websocket connect attempts can block
    the UI. This service retries on a cooldown instead of hammering OBS every tick.
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.client = None

        self.connect_timeout_seconds = 1
        self.retry_cooldown_seconds = 15
        self.next_retry_epoch = 0.0
        self.last_error = ""

    def connect(self):
        from obsws_python import ReqClient

        self.client = ReqClient(
            host=self.host,
            port=self.port,
            password=self.password,
            timeout=self.connect_timeout_seconds,
        )

    @staticmethod
    def _attr(obj, *names, default=None):
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
        return default

    def snapshot(self) -> ObsSnapshot:
        snap = ObsSnapshot()

        now = time.time()

        if self.client is None and now < self.next_retry_epoch:
            remaining = int(self.next_retry_epoch - now)
            snap.error = (
                f"OBS disconnected. Retrying in {remaining}s. Last error: {self.last_error}"
            )
            return snap

        try:
            if self.client is None:
                self.connect()

            stats = self.client.get_stats()
            scene = self.client.get_current_program_scene()
            stream_status = self.client.get_stream_status()
            record_status = self.client.get_record_status()

            snap.connected = True
            snap.streaming = bool(
                self._attr(stream_status, "output_active", "outputActive", default=False)
            )
            snap.recording = bool(
                self._attr(record_status, "output_active", "outputActive", default=False)
            )
            snap.current_scene = self._attr(
                scene,
                "current_program_scene_name",
                "currentProgramSceneName",
                default="Unknown",
            )

            snap.fps = self._attr(stats, "active_fps", "activeFps")
            snap.cpu_usage = self._attr(stats, "cpu_usage", "cpuUsage")
            snap.memory_usage_mb = self._attr(stats, "memory_usage", "memoryUsage")

            snap.render_missed_frames = self._attr(
                stats,
                "render_missed_frames",
                "renderMissedFrames",
                default=0,
            )
            snap.render_total_frames = self._attr(
                stats,
                "render_total_frames",
                "renderTotalFrames",
                default=0,
            )
            snap.output_skipped_frames = self._attr(
                stats,
                "output_skipped_frames",
                "outputSkippedFrames",
                default=0,
            )
            snap.output_total_frames = self._attr(
                stats,
                "output_total_frames",
                "outputTotalFrames",
                default=0,
            )

            if snap.render_total_frames:
                snap.render_lag_percent = round(
                    (snap.render_missed_frames / snap.render_total_frames) * 100,
                    2,
                )

            if snap.output_total_frames:
                snap.encoding_lag_percent = round(
                    (snap.output_skipped_frames / snap.output_total_frames) * 100,
                    2,
                )

            self.last_error = ""
            self.next_retry_epoch = 0.0
            return snap

        except Exception as exc:
            self.client = None
            self.last_error = str(exc)
            self.next_retry_epoch = time.time() + self.retry_cooldown_seconds

            snap.connected = False
            snap.error = self.last_error
            return snap
