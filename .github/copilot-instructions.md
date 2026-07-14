# GitHub Copilot Instructions for StreamPilot

You are assisting with StreamPilot, an open-source Creator Intelligence Platform.

## Core Mission

Help creators improve every stream through thoughtful intelligence, reliable tools, and creator-first design.

## Required Project Principles

Follow these principles in all suggestions:

- Creator First
- Local First
- AI is Optional
- Security by Design
- Simplicity Over Cleverness
- Clear Boundaries
- Fail Gracefully
- Documentation Is Part of the Product
- Preserve Existing Creator Workflows

## Architecture Expectations

Prefer this conceptual flow:

```text
Presentation
    ↓
Services
    ↓
Event Bus
    ↓
Connectors / Intelligence / Storage
    ↓
External Services
```

Do not suggest UI code that directly calls external APIs, stores secrets, or performs connector internals.

Prefer service abstractions and documented interfaces.

## Intelligence Expectations

Use this model:

```text
Events
    ↓
Analytics
    ↓
Insights
    ↓
Recommendations
    ↓
Reports / Mission Control / Producer
```

Reports should stay factual.

Producer may interpret reports.

AI may enhance intelligence, but AI must remain optional.

## Security Rules

Never generate code that logs, prints, exposes, stores insecurely, or commits:

- API keys
- OAuth tokens
- Discord webhook URLs
- OBS passwords
- Authentication headers
- Session cookies

Secrets should go through a centralized configuration or secret-management layer.

## Existing Dashboard

Do not treat the current dashboard as disposable.

It should evolve into Mission Control.

Prefer incremental refactoring over rewriting.

## When Reviewing Code

Call out:

- Tight coupling
- Direct UI-to-API calls
- Missing error handling
- Secret exposure
- AI-required workflows
- Missing documentation
- Missing tests
- Runtime data accidentally being committed
- Build artifacts being tracked

## When Writing Code

Prefer:

- Small functions
- Typed interfaces when practical
- Clear names
- Explicit configuration
- Graceful fallback behavior
- Tests for business logic
- Documentation updates for user-facing changes

## North Star

Every stream should make the next stream better.
