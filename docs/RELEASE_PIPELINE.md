# v0.2.1 Release Pipeline

This release adds automated GitHub release assets.

When a tag like `v0.2.1` is pushed, GitHub Actions builds:

```text
DadR3x_Command_Center_v0.2.1_Source.zip
DadR3x_Command_Center_v0.2.1_Windows.zip
DadR3x_Command_Center_v0.2.1_macOS.zip
```

Each ZIP also gets a `.sha256` checksum.

## Required file locations

Important: place the workflow here exactly:

```text
.github/workflows/release.yml
```

The ZIP bundle includes it as:

```text
COPY_THIS_TO_.github_workflows/release.yml
```

because hidden folders can be awkward in some zip viewers.

## Tag flow

After this is merged to `main`:

```bash
git checkout main
git pull origin main
git tag -a v0.2.1 -m "Release automation pipeline"
git push origin v0.2.1
```
