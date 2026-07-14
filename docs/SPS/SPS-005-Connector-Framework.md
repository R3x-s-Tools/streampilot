# SPS-005 — Connector Framework

**Status:** Approved  
**Version:** 1.0

## Definition

A connector communicates with one external system.

Examples:

- OBS
- Twitch
- Discord
- Streamer.bot
- YouTube
- Kick
- AI providers

## Responsibilities

Connectors establish connections, authenticate, monitor health, receive external events, translate them into StreamPilot events, and shut down gracefully.

## Non-Responsibilities

Connectors do not perform analytics, generate reports, make UI decisions, store long-term state, or directly access unrelated connectors.

## Compatibility

Connectors should support migration paths and avoid breaking creators when external APIs change.

## Principle

Connectors are reliable translators.
