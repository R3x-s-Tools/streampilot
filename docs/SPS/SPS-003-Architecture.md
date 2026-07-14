# SPS-003 — Architecture

**Status:** Approved  
**Version:** 1.0

## Principles

- Modular by Default
- Local First
- Security by Design
- Event Driven
- Platform Agnostic

## Layers

- Presentation Layer
- Service Layer
- Event Bus
- Connector Layer
- Intelligence Layer
- Storage Layer

## Dependency Rule

Presentation depends on services. Services depend on core abstractions. Infrastructure implements abstractions. Lower layers do not depend on higher layers.

## Security Zones

- UI
- Application Services
- Connectors
- Secret Storage
- Local Data Store
- External Services

## Guiding Principle

Prefer simplicity, modularity, and clear boundaries over short-term convenience.
