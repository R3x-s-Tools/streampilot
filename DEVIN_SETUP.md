# Set Up Devin for StreamPilot

## 1. Connect GitHub
In Devin:
1. Open Settings.
2. Open Integrations.
3. Connect GitHub.
4. Grant access to the StreamPilot repository.
5. Index the repository if prompted.

## 2. Add the OpenAI API Key Safely
Do not add the key to GitHub, source code, prompts, issues, or chat messages.

In Devin's repository environment configuration:
1. Open the StreamPilot repository environment or snapshot configuration.
2. Add a repository-scoped environment variable or secret.
3. Name it:
```text
OPENAI_API_KEY
```
4. Paste the key as the value.
5. Save the environment configuration.
6. Start a new Devin session using that environment.

The application should read it with:
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
```

## 3. Verify Without Revealing the Key
Ask Devin to run:
```bash
python -c "import os; print('configured' if os.getenv('OPENAI_API_KEY') else 'missing')"
```

Expected:
```text
configured
```

Never print the key itself.

## 4. Start the Review
Paste:
```text
Read AGENTS.md, PROJECT.md, ai/AI_CONTEXT.md, and docs/SPS/SPS-000-Manifesto.md through docs/SPS/SPS-014-Engineering-Principles.md.

Then perform the review in ai/prompts/DEVIN_PROJECT_REVIEW.md.

Do not change code. Return the architectural review first.
```
