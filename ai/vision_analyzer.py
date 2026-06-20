from __future__ import annotations

import base64
import time
from pathlib import Path


class VisionAnalyzer:
    """
    Lightweight AI vision scaffold.

    It is intentionally conservative:
    - disabled unless provider=openai and api_key exists
    - runs only when called by the UI timer
    - receives still preview frames, not video
    """

    def __init__(self, provider: str = "off", api_key: str = "", model: str = "gpt-4.1-mini"):
        self.provider = (provider or "off").lower()
        self.api_key = api_key or ""
        self.model = model or "gpt-4.1-mini"
        self.last_error = ""
        self.last_analysis_epoch = 0.0

    def analyze_frame(self, image_path: str, context: str = "") -> str:
        if self.provider != "openai" or not self.api_key:
            return "AI vision is disabled. Set AI_PROVIDER=openai and OPENAI_API_KEY to enable frame analysis."

        path = Path(image_path)
        if not path.exists():
            return "AI vision could not find the preview frame."

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            encoded = base64.b64encode(path.read_bytes()).decode("utf-8")

            prompt = f"""
You are a live stream producer assistant for Dad_R3x.

Analyze this single OBS preview frame. Do NOT pretend you know motion or audio.
Return max 3 bullets starting with 🦖.

Focus on:
- Is this a gameplay moment, menu, loading screen, dead air, or stream scene?
- Is this worth marking as a clip?
- What should the streamer do next?

Context:
{context}
"""

            response = client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{encoded}",
                            },
                        ],
                    }
                ],
            )

            self.last_analysis_epoch = time.time()
            self.last_error = ""
            return response.output_text.strip()

        except Exception as exc:
            self.last_error = str(exc)
            return f"AI vision error: {exc}"
