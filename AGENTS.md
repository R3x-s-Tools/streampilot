# StreamPilot Agent Instructions

## Project
StreamPilot is an open-source Creator Intelligence Platform.

Tagline: Never Stream Alone.

Mission: Help creators improve every stream through thoughtful intelligence, reliable tools, and creator-first design.

## Required Reading
Before changing code, read:
1. PROJECT.md
2. ai/AI_CONTEXT.md
3. docs/SPS/SPS-000-Manifesto.md
4. docs/SPS/SPS-003-Architecture.md
5. docs/SPS/SPS-004-Security.md
6. docs/SPS/SPS-006-Intelligence-Engine.md
7. docs/SPS/SPS-014-Engineering-Principles.md

## Core Rules
- Preserve working creator workflows.
- The current dashboard evolves into Mission Control.
- Prefer incremental refactoring over rewrites.
- Keep AI optional.
- Reports remain factual.
- Producer interprets reports.
- Never expose or log secrets.
- Keep connectors isolated.
- Prefer small, testable components.
- Update documentation when behavior changes.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Tests
```bash
pytest
python -m black --check .
python -m ruff check .
```

## Security
Never commit or print:
- OPENAI_API_KEY
- OAuth tokens
- Discord webhook URLs
- OBS passwords
- Authentication headers
- Session cookies

Use environment variables or Devin repository-scoped secrets.

## North Star
Every stream should make the next stream better.
