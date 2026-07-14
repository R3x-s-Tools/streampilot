# Apply StreamPilot Foundation Transition Pack

This pack is designed to be safe.

It adds documentation, governance, templates, and structure. It does **not** delete the existing dashboard or app code.

## Recommended branch

```bash
cd ~/Documents/dadr3x_command_center_pro
git checkout main
git pull origin main
git checkout -b chore/streampilot-foundation
```

## Copy files

Unzip this pack, then copy everything into your repository root.

Example:

```bash
cp -R /path/to/StreamPilot_Foundation_Transition_Pack_v0.3.0-dev1/. .
```

## Review

```bash
git status
git diff --stat
```

## Commit

```bash
git add README.md PROJECT.md CONTRIBUTING.md SECURITY.md SUPPORT.md CHANGELOG.md DECISIONS.md CODE_OF_CONDUCT.md LICENSE ROADMAP.md .editorconfig .github docs assets examples plugins tools scripts .gitignore.stream_pilot_recommended
git commit -m "Add StreamPilot foundation and governance"
git push origin chore/streampilot-foundation
```

## Open a PR

PR title:

```text
Add StreamPilot foundation and governance
```

## Important

This pack intentionally does not rename Python packages or remove existing application code.
The current dashboard remains intact and will evolve into Mission Control later.
