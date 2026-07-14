import json
from pathlib import Path


def generate_ai_report(ai_client, analytics_json_path):
    prompt = Path("ai/report_prompt.md").read_text()
    payload = json.loads(Path(analytics_json_path).read_text())
    return ai_client.generate(system=prompt, data=payload)
