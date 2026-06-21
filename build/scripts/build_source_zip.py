from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

EXCLUDED_NAMES = {
    ".git",
    ".github",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "__MACOSX",
    ".DS_Store",
    ".env",
    "logs",
    "stream_logs",
    "stream_reports",
    "dist",
    "build",
    "release",
    ".pyinstaller_build",
}

EXCLUDED_RELATIVE_FILES = {
    "data/twitch_tokens.json",
    "data/viewer_memory.json",
}


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)

    if any(part in EXCLUDED_NAMES for part in rel.parts):
        return True

    if str(rel) in EXCLUDED_RELATIVE_FILES:
        return True

    if path.suffix in {".pyc", ".pyo"}:
        return True

    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="local")
    args = parser.parse_args()

    root = Path.cwd()
    release_dir = root / "release"
    package_dir = release_dir / "DadR3x_Command_Center"
    zip_path = release_dir / f"DadR3x_Command_Center_{args.version}_Source.zip"

    if release_dir.exists():
        shutil.rmtree(release_dir)

    package_dir.mkdir(parents=True)

    for path in root.rglob("*"):
        if should_skip(path, root):
            continue

        rel = path.relative_to(root)
        dest = package_dir / rel

        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    (package_dir / "RELEASE.txt").write_text(
        f"""Dad_R3x Command Center Pro
Version: {args.version}

Source package setup:
1. Copy .env.example to .env
2. Fill in Twitch and OBS settings
3. Create a virtual environment
4. pip install -r requirements.txt
5. python app.py

Never share .env or data/twitch_tokens.json.
""",
        encoding="utf-8",
    )

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for item in package_dir.rglob("*"):
            z.write(item, item.relative_to(release_dir))

    print(f"Built {zip_path}")


if __name__ == "__main__":
    main()
