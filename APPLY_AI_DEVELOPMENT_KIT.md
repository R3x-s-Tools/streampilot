# Apply the StreamPilot AI Development Kit

## Copy Into Repository
```bash
cd ~/Documents/dadr3x_command_center_pro
cp -R ~/Downloads/StreamPilot_AI_Development_Kit/. .
```

## Verify
```bash
ls AGENTS.md
ls DEVIN.md
ls DEVIN_SETUP.md
ls ai/AI_CONTEXT.md
ls ai/prompts/DEVIN_PROJECT_REVIEW.md
ls .github/copilot-instructions.md
```

## Commit
```bash
git add AGENTS.md DEVIN.md DEVIN_SETUP.md CLAUDE.md .cursorrules ai .github/copilot-instructions.md
git commit -m "docs: add AI development guidance"
```

Do not commit OPENAI_API_KEY.
