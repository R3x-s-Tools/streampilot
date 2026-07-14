from __future__ import annotations

import argparse
from pathlib import Path

from reports.report_summary import parse_deep_analytics_report
from services.discord_reporter import DiscordReporter

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def find_latest_report(report_dir: Path) -> Path:
    reports = sorted(report_dir.glob("deep_analytics_report_*.md"), key=lambda p: p.stat().st_mtime)
    if not reports:
        raise SystemExit(f"No deep analytics reports found in {report_dir}")
    return reports[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Send latest StreamPilot report to Discord.")
    parser.add_argument("--report-dir", default="stream_reports")
    parser.add_argument("--report", default="")
    parser.add_argument("--no-attach", action="store_true")
    args = parser.parse_args()

    report_path = Path(args.report) if args.report else find_latest_report(Path(args.report_dir))
    summary = parse_deep_analytics_report(report_path)
    sent = DiscordReporter().send_markdown_report(
        report_path=report_path,
        summary=summary,
        attach_report=not args.no_attach,
    )

    if sent:
        print(f"Sent Discord report: {report_path}")
    else:
        print("Discord report not sent: DISCORD_REPORT_WEBHOOK_URL is not configured")


if __name__ == "__main__":
    main()
