# Connector Framework Refactoring

## Overview

This document describes the refactoring of the OBS service into the Connector Framework, as specified in SPS-005.

## Purpose

To align the OBS integration with the StreamPilot architecture (SPS-003) by implementing the Connector Framework pattern, providing:
- Standardized connector interface
- Better separation of concerns
- Improved testability
- Foundation for future connectors (Twitch, Discord, etc.)

## Architecture Changes

OBS status now also follows the event-driven application path:

```text
OBSConnector
    ↓ ConnectorEvent
EventBus (connector.status / connector.obs.status)
    ↓
MissionControlReadModel
```

The existing `get_snapshot()` polling API remains available during migration. Each
poll emits the same factual connector event, allowing Mission Control consumers to
move to the read model without disrupting the current dashboard.

### Before

```
services/obs_service.py (ObsService)
    ↓
services/application_services.py (uses ObsService directly)
    ↓
ui/main_window.py (uses ObsService directly)
```

### After

```
core/connectors/base.py (Connector abstract base class)
    ↓
connectors/obs_connector.py (OBSConnector implements Connector)
    ↓ wraps
services/obs_service.py (ObsService - preserved for backwards compatibility)
    ↓
services/application_services.py (uses OBSConnector)
    ↓
ui/main_window.py (uses OBSConnector via SessionPresenter)
```

## Files Changed

### New Files Created

1. **core/connectors/__init__.py**
   - Exports Connector and ConnectorStatus

2. **core/connectors/base.py**
   - Defines Connector abstract base class
   - Defines ConnectorStatus dataclass
   - Defines ConnectionState enum
   - Implements SPS-005 connector responsibilities

3. **connectors/__init__.py**
   - Exports OBSConnector

4. **connectors/obs_connector.py**
   - OBSConnector implements Connector interface
   - Wraps existing ObsService for backwards compatibility
   - Provides standardized status reporting
   - Maintains all existing ObsService functionality

5. **tests/test_connector_base.py**
   - Tests for Connector base class
   - Tests for ConnectorStatus
   - Tests for ConnectionState enum

6. **tests/test_obs_connector.py**
   - Tests for OBSConnector
   - Tests for backwards compatibility with ObsService

### Modified Files

1. **services/application_services.py**
   - Changed import from `ObsService` to `OBSConnector`
   - Changed type hint from `ObsService` to `OBSConnector`
   - Changed instantiation from `ObsService` to `OBSConnector`

2. **ui/main_window.py**
   - Changed import to include `OBSConnector`
   - No functional changes to UI code

3. **ui/session_presenter.py**
   - Added backwards compatibility check for `get_snapshot()` method
   - Supports both ObsService and OBSConnector interfaces

4. **core/__init__.py**
   - Added exports for Connector and ConnectorStatus

### Unchanged Files

- **services/obs_service.py** - Preserved exactly as-is for backwards compatibility
- **services/obs_preview_service.py** - No changes required
- **tests/test_obs_service.py** - All existing tests still pass

## Backwards Compatibility

The refactoring maintains 100% backwards compatibility:

1. **ObsService preserved**: The original `ObsService` class remains unchanged in `services/obs_service.py`

2. **OBSConnector wraps ObsService**: The new `OBSConnector` wraps the existing `ObsService`, exposing it via the `obs_service` property

3. **SessionPresenter compatibility**: The `SessionPresenter._update_obs()` method detects whether it's using `ObsService` or `OBSConnector` and calls the appropriate method (`snapshot()` or `get_snapshot()`)

4. **ObsPreviewService unchanged**: The `ObsPreviewService` continues to work with the wrapped `ObsService` without modification

5. **All existing tests pass**: The original `test_obs_service.py` tests continue to pass without modification

## Connector Framework Design

Per SPS-005, connectors:

### Responsibilities
- Establish connections to external systems
- Authenticate with external systems
- Monitor health
- Receive external events
- Translate events to StreamPilot events
- Shut down gracefully

### Non-Responsibilities
- Do NOT perform analytics
- Do NOT generate reports
- Do NOT make UI decisions
- Do NOT store long-term state
- Do NOT directly access unrelated connectors

### Implementation

The `Connector` base class defines the standard interface:
- `connect()` - Establish connection
- `disconnect()` - Gracefully disconnect
- `is_connected()` - Check connection status
- `get_status()` - Get detailed status information
- `health_check()` - Perform health check

`ConnectorStatus` provides standardized status reporting:
- `state` - ConnectionState enum (DISCONNECTED, CONNECTING, CONNECTED, ERROR)
- `connected` - Boolean connection status
- `error` - Current error message
- `last_error` - Last error encountered
- `metadata` - Dict for connector-specific information

## Testing

### Test Coverage

1. **test_connector_base.py** (10 tests)
   - Connector initialization
   - Connection success/failure scenarios
   - Disconnect behavior
   - Health check functionality
   - Status metadata handling
   - Enum validation

2. **test_obs_connector.py** (9 tests)
   - OBSConnector initialization
   - ObsService wrapping verification
   - Backwards compatibility with get_snapshot()
   - Connection status reporting
   - Disconnect behavior
   - Health check functionality
   - Connection attempt tracking
   - Metadata inclusion

3. **test_obs_service.py** (2 existing tests)
   - All existing tests continue to pass

### Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/test_connector_base.py -v
python -m pytest tests/test_obs_connector.py -v
python -m pytest tests/test_obs_service.py -v
```

## Migration Path

For future connectors (Twitch, Discord, etc.):

1. Create connector class in `connectors/` directory
2. Extend `Connector` base class
3. Implement required abstract methods
4. Wrap existing service if one exists (for backwards compatibility)
5. Add tests in `tests/` directory
6. Update `ApplicationServices` to use new connector
7. Update documentation

## Benefits

1. **Architecture Alignment**: Aligns with SPS-003 architecture layers
2. **Standardization**: Provides consistent interface for all external system connections
3. **Testability**: Abstract base class makes testing easier and more consistent
4. **Maintainability**: Clear separation between connector logic and business logic
5. **Extensibility**: Easy to add new connectors following the same pattern
6. **Backwards Compatibility**: No breaking changes to existing functionality
7. **Documentation**: Clear contract for what connectors should and shouldn't do

## Risks and Mitigations

### Risk: Breaking existing functionality
**Mitigation**: ObsService preserved unchanged, OBSConnector wraps it, all existing tests pass

### Risk: Performance overhead
**Mitigation**: Minimal overhead - OBSConnector is a thin wrapper around existing ObsService

### Risk: Confusion between ObsService and OBSConnector
**Mitigation**: Clear documentation, backwards compatibility in SessionPresenter, gradual migration path

### Risk: Future connectors may not follow pattern
**Mitigation**: Abstract base class enforces interface, tests provide examples, documentation explains pattern

## Next Steps

1. Monitor OBSConnector in production for any issues
2. Consider migrating other services (Twitch, Discord) to Connector Framework
3. Add event translation capabilities to connectors per SPS-005
4. Consider adding connector lifecycle events to EventBus
