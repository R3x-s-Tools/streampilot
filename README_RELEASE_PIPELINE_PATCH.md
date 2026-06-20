# Release Pipeline Patch

Copy these files into your repo:

```text
.github/workflows/release.yml
DadR3xCommandCenter.spec
docs/RELEASE_PIPELINE.md
```

## Commit to develop

```bash
git checkout develop
git pull origin develop
git add .github/workflows/release.yml DadR3xCommandCenter.spec docs/RELEASE_PIPELINE.md
git commit -m "Add automated release build pipeline"
git push origin develop
```

## Merge to main

Open PR:

```text
develop -> main
```

Wait for CI, then merge.

## Tag release

```bash
git checkout main
git pull origin main
git tag -a v0.2.0 -m "Producer Console Release"
git push origin v0.2.0
```

## Expected release files

GitHub should attach:

```text
DadR3x_Command_Center_v0.2.0_Source.zip
DadR3x_Command_Center_v0.2.0_Windows.zip
DadR3x_Command_Center_v0.2.0_macOS.zip
```

plus `.sha256` checksum files.
