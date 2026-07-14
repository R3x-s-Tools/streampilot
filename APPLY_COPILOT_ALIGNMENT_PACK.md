# Apply StreamPilot Copilot Alignment Pack

This pack adds persistent AI assistant guidance to the repository.

It does not modify application code.

## Files Included

```text
ai/AI_CONTEXT.md
ai/prompts/COPILOT_PROJECT_REVIEW_PROMPT.md
.github/copilot-instructions.md
```

## Recommended Branch

```bash
cd ~/Documents/dadr3x_command_center_pro
git checkout chore/streampilot-foundation
```

If that branch does not exist:

```bash
git checkout -b chore/streampilot-foundation
```

## Copy Files Into Repo

If this pack is extracted in Downloads:

```bash
cd ~/Documents/dadr3x_command_center_pro
cp -R ~/Downloads/StreamPilot_Copilot_Alignment_Pack/. .
```

## Verify

```bash
ls ai/AI_CONTEXT.md
ls ai/prompts/COPILOT_PROJECT_REVIEW_PROMPT.md
ls .github/copilot-instructions.md
git status
```

## Commit

```bash
git add ai/AI_CONTEXT.md ai/prompts/COPILOT_PROJECT_REVIEW_PROMPT.md .github/copilot-instructions.md
git commit -m "docs: add Copilot alignment context"
```

## How To Use With Copilot Chat

Open Copilot Chat in VS Code and paste:

```text
Read ai/AI_CONTEXT.md, PROJECT.md, and docs/SPS/SPS-000-Manifesto.md through docs/SPS/SPS-014-Engineering-Principles.md.

Then review this repository using ai/prompts/COPILOT_PROJECT_REVIEW_PROMPT.md.

Do not rewrite code yet. First provide an architectural review, prioritized recommendations, and safe next steps.
```

## Best Use

Use this before large refactors, architecture work, or Project Compass planning.

Do not ask Copilot to rewrite the whole project.

Ask for small, safe, Foundation-aligned changes.
