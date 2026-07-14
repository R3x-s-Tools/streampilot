# Continuous Integration

Pull requests into `main` or `develop` run required code-quality and platform checks.

## Quality gates

- Ruff linting
- Black formatting
- Full pytest suite with a 45% aggregate coverage floor
- Import smoke tests
- Full tests on Ubuntu, macOS, and Windows with Python 3.12
- Headless Qt runtime dependencies installed on Linux so UI components are tested rather than skipped
- A guard that rejects `data/twitch_tokens.json` if it is ever tracked

Install the development dependencies locally:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Run the same quality checks used by CI:

```bash
python -m ruff check .
python -m black --check .
python -m pytest \
  --cov=ai --cov=analytics --cov=connectors --cov=core \
  --cov=reports --cov=services --cov=ui \
  --cov-report=term-missing --cov-fail-under=45
```

## Branch protection

After the workflow has run, configure the `main` branch protection rule in GitHub to require:

- `Quality and coverage`
- `Tests (ubuntu-latest)`
- `Tests (macos-latest)`
- `Tests (windows-latest)`
- `docs-check`

Also require pull requests and require branches to be current before merging. Limit bypass access to
repository emergency administrators.
