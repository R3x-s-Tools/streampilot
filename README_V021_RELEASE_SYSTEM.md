# v0.2.1 Release System Patch

Copy these files:

```text
COPY_THIS_TO_.github_workflows/release.yml
DadR3xCommandCenter.spec
docs/RELEASE_PIPELINE.md
```

But the workflow file must land here:

```text
.github/workflows/release.yml
```

## Terminal copy command

From your repo root, after unzipping this patch:

```bash
mkdir -p .github/workflows
cp COPY_THIS_TO_.github_workflows/release.yml .github/workflows/release.yml
cp DadR3xCommandCenter.spec ./DadR3xCommandCenter.spec
cp docs/RELEASE_PIPELINE.md ./docs/RELEASE_PIPELINE.md
```

## Commit

```bash
git checkout develop
git pull origin develop
git add .github/workflows/release.yml DadR3xCommandCenter.spec docs/RELEASE_PIPELINE.md
git commit -m "Add v0.2.1 release automation pipeline"
git push origin develop
```

Open PR:

```text
develop -> main
```

After merge:

```bash
git checkout main
git pull origin main
git tag -a v0.2.1 -m "Release automation pipeline"
git push origin v0.2.1
```
