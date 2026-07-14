# StreamPilot AI Context

## Purpose

This document provides persistent project context for AI coding assistants working on StreamPilot.

Use this alongside the official StreamPilot Specification documents in `docs/SPS/`.

---

## Project

**Name:** StreamPilot  
**Category:** Creator Intelligence Platform  
**Tagline:** Never Stream Alone.

---

## Mission

Help creators improve every stream through thoughtful intelligence, reliable tools, and creator-first design.

---

## Vision

Become the most trusted open-source Creator Intelligence Platform while respecting creator ownership, privacy, and creativity.

---

## Core Principles

Always prioritize:

- Creator First
- Local First
- AI is Optional
- Security by Design
- Simplicity
- Reliability
- Transparency
- Community
- Open Source
- Never Stream Alone

---

## Product Philosophy

StreamPilot exists to help creators make better decisions.

It does not exist to automate creativity.

Every feature should improve creator confidence without taking control away from them.

---

## Engineering Philosophy

Prefer:

- Small components
- Event-driven design
- Clear interfaces
- Modular architecture
- Testable code
- Explicit behavior
- Graceful failure
- Documentation

Avoid:

- Large monolithic classes
- Hidden behavior
- Tight coupling
- Unnecessary dependencies
- Premature optimization
- Rewrites without a clear architectural reason

---

## Architecture

Primary conceptual layers:

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

Subsystems should communicate through documented interfaces.

The UI should not directly call external APIs, secret storage, or connector internals.

---

## Intelligence Model

```text
Events
    ↓
Analytics
    ↓
Insights
    ↓
Recommendations
    ↓
Reports / Mission Control / Producer Presentation
```

Reports remain factual.

Producer interprets reports.

AI may enhance intelligence, but AI is never required.

---

## Creator Rights

Always preserve:

- Data ownership
- Privacy
- Exportability
- Transparency
- Offline capability whenever practical
- Control over integrations and AI providers

---

## AI Policy

AI is optional.

Never require cloud AI to use StreamPilot.

All AI functionality should fail gracefully.

Prefer structured analytics data over asking AI to infer meaning from raw text.

---

## Existing Application

The current dashboard is not throwaway legacy code.

It is the beginning of Mission Control.

Prefer incremental refactoring over rewriting.

No working feature should be removed or rewritten without a compelling architectural reason.

---

## Security Rules

Never expose or log:

- API keys
- OAuth tokens
- Discord webhooks
- OBS passwords
- Authentication headers
- Session cookies
- Secret file paths containing credentials

Secrets should flow through a centralized secret-management layer.

---

## Documentation

Before changing architecture, review:

- `PROJECT.md`
- `docs/SPS/SPS-000-Manifesto.md`
- `docs/SPS/SPS-003-Architecture.md`
- `docs/SPS/SPS-004-Security.md`
- `docs/SPS/SPS-006-Intelligence-Engine.md`
- `docs/SPS/SPS-014-Engineering-Principles.md`

---

## Contributor Expectations

When implementing code:

- Explain architectural tradeoffs.
- Recommend simpler alternatives when appropriate.
- Preserve backward compatibility whenever practical.
- Keep creator workflows stable.
- Update documentation when behavior changes.
- Add or update tests when practical.

---

## North Star

Every stream should make the next stream better.
