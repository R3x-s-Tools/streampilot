# Devin Project Review Prompt

Read:
- AGENTS.md
- PROJECT.md
- ai/AI_CONTEXT.md
- docs/SPS/SPS-000-Manifesto.md through docs/SPS/SPS-014-Engineering-Principles.md

Review the repository without changing code.

Evaluate:
1. Repository structure
2. Current dashboard and Mission Control alignment
3. Architecture and coupling
4. Configuration and secrets
5. Connectors
6. Analytics and reports
7. Intelligence and optional AI
8. Testing
9. Packaging and release workflow
10. Runtime data and build artifacts

Return:
- Architecture score from 0 to 100
- Foundation alignment
- Top five risks
- Top five safe improvements
- Quick wins
- Technical debt
- Security concerns
- Recommended first implementation milestone

For each recommendation, cite the relevant SPS document and propose the smallest safe change.

Do not rewrite code yet.
