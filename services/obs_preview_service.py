from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PreviewFrame:
    ok: bool
    image_path: Optional[str] = None
    source_name: str = ""
    error: str = ""


class ObsPreviewService:
    """
    Captures still preview frames from OBS over WebSocket.

    This version supports multiple obsws-python get_source_screenshot signatures.
    """

    def __init__(self, obs_service, output_dir: str = "data/preview_frames"):
        self.obs_service = obs_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_frame_path = self.output_dir / "latest_preview.png"
        self.last_error = ""

    def capture_current_scene(self, width: int = 960, height: int = 540) -> PreviewFrame:
        try:
            if self.obs_service.client is None:
                self.obs_service.connect()

            scene_response = self.obs_service.client.get_current_program_scene()
            source_name = self._attr(
                scene_response,
                "current_program_scene_name",
                "currentProgramSceneName",
                default="",
            )

            if not source_name:
                return PreviewFrame(False, error="Could not determine current OBS scene.")

            image_data = self._get_source_screenshot(source_name, width, height)

            if not image_data:
                return PreviewFrame(
                    False,
                    source_name=source_name,
                    error="OBS did not return screenshot image data.",
                )

            image_bytes = self._decode_image_data(image_data)
            self.last_frame_path.write_bytes(image_bytes)
            self.last_error = ""

            return PreviewFrame(
                ok=True,
                image_path=str(self.last_frame_path),
                source_name=source_name,
            )

        except Exception as exc:
            self.last_error = str(exc)
            return PreviewFrame(False, error=str(exc))

    def _get_source_screenshot(self, source_name: str, width: int, height: int):
        client = self.obs_service.client

        if not hasattr(client, "get_source_screenshot"):
            return self._get_source_screenshot_raw(source_name, width, height)

        method = client.get_source_screenshot

        attempts = [
            # Newer snake_case style
            lambda: method(
                source_name=source_name,
                image_format="png",
                image_width=width,
                image_height=height,
            ),
            # Older/camelCase style
            lambda: method(
                sourceName=source_name,
                imageFormat="png",
                imageWidth=width,
                imageHeight=height,
            ),
            # Positional style used by some obsws-python versions
            lambda: method(source_name, "png", width, height),
            # Minimal args
            lambda: method(source_name, "png"),
        ]

        errors = []

        for attempt in attempts:
            try:
                response = attempt()
                return self._extract_image_data(response)
            except TypeError as exc:
                errors.append(str(exc))
                continue

        # Last fallback: raw request if the client exposes it.
        try:
            return self._get_source_screenshot_raw(source_name, width, height)
        except Exception as exc:
            errors.append(str(exc))

        raise RuntimeError(
            "Could not call OBS GetSourceScreenshot. Attempts: " + " | ".join(errors[-4:])
        )

    def _get_source_screenshot_raw(self, source_name: str, width: int, height: int):
        client = self.obs_service.client

        payload = {
            "sourceName": source_name,
            "imageFormat": "png",
            "imageWidth": width,
            "imageHeight": height,
        }

        if hasattr(client, "send"):
            response = client.send("GetSourceScreenshot", payload)
            return self._extract_image_data(response)

        if hasattr(client, "call"):
            response = client.call("GetSourceScreenshot", payload)
            return self._extract_image_data(response)

        raise RuntimeError("obsws-python client does not expose send/call raw request fallback.")

    def _extract_image_data(self, response):
        if isinstance(response, dict):
            return response.get("imageData") or response.get("image_data")

        return self._attr(response, "image_data", "imageData")

    @staticmethod
    def _decode_image_data(image_data: str) -> bytes:
        if image_data.startswith("data:image"):
            image_data = image_data.split(",", 1)[1]
        return base64.b64decode(image_data)

    @staticmethod
    def _attr(obj, *names, default=None):
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
        return default
