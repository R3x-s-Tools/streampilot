# StreamPilot AI Context

## Identity
- Name: StreamPilot
- Category: Creator Intelligence Platform
- Tagline: Never Stream Alone.

## Architecture
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
Reports / Mission Control / Producer
```

## Hard Requirements
- Creator First
- Local First
- AI Optional
- Security by Design
- Graceful Failure
- Clear Boundaries
- Backward Compatibility When Practical
- Documentation Is Part of the Product

## Existing Application
The current dashboard remains in place and evolves into Mission Control.

Prefer safe migration and incremental refactoring.

## AI
OpenAI integration must read OPENAI_API_KEY from the environment or a secure secret store.

Never hardcode keys.

## Creator Data
Creator data belongs to the creator.

Do not transmit or persist unnecessary data.
