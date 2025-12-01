# Enhanced Logging for Identity Config Operator and Listener

## Overview

This document describes the comprehensive logging enhancements added to the Identity Config Operator and Identity Listener to provide better visibility into Hub POST registrations and notification processing.

## Changes Made

### 1. Identity Config Operator (`identityConfigOperatorKeycloak.py`)

#### Enhanced Hub Registration Logging
- **Enhanced `register_listener()` function**:
  - Added `api_type` parameter to identify which API is being registered
  - Comprehensive logging of registration attempts, success, and failures
  - Detailed error handling with specific error messages
  - Debug logging of request payloads and responses

#### Listener Registry System
- **Global listener registry**: Tracks all registered listeners across all components
- **Functions added**:
  - `add_to_listener_registry()`: Adds listeners to global registry with timestamps
  - `remove_from_listener_registry()`: Removes listeners when components are deleted
  - `log_all_registered_listeners()`: Displays current state of all registered listeners

#### Periodic Monitoring
- **Timer-based summary**: Every 5 minutes, logs all registered listeners
- **Health check probe**: Provides health status and listener count
- **Automatic cleanup**: Registry is updated when components are created/deleted

### 2. Identity Listener (`identity-listener-keycloak.py`)

#### Comprehensive Notification Logging
- **Enhanced notification reception logging**:
  - Logs source IP, User-Agent, Content-Type for each notification
  - Identifies notification type (partyRole vs permissionSpecificationSet)
  - Extracts and logs key details (name, href) from notifications
  - Clear start/end markers for notification processing

#### Status Endpoint
- **New `/status` endpoint**: 
  - GET endpoint for monitoring listener health
  - Tests Keycloak connectivity
  - Shows environment configuration
  - Useful for debugging and monitoring

## Logging Output Examples

### Hub Registration
```
INFO - Registering listener for partyRoleAPI - Hub URL: http://component.namespace.svc.cluster.local:8080/path/hub
DEBUG - Registration payload: {"callback": "http://idlistkey.canvas:5000/listener", "@type": "Hub"}
INFO - Successfully registered listener for partyRoleAPI at http://component.namespace.svc.cluster.local:8080/path/hub
INFO - Added partyRoleAPI listener for component example-component to registry
INFO - Current registered listeners: ['example-component']
```

### Listener Registry Summary
```
INFO - Currently registered listeners for 2 components:
INFO -   - Component: component1, API: partyRoleAPI, URL: http://comp1.ns.svc.cluster.local:8080/api/hub, Registered: 2025-06-29T10:30:00
INFO -   - Component: component2, API: permissionSpecificationSetAPI, URL: http://comp2.ns.svc.cluster.local:8080/permissions/hub, Registered: 2025-06-29T10:35:00
```

### Notification Processing
```
INFO - === NOTIFICATION RECEIVED ===
INFO - Received notification from: 10.244.1.5
INFO - User-Agent: TMForum-Component/1.0
INFO - Content-Type: application/json
INFO - Event Type: PartyRoleCreationNotification
INFO - Notification Source: partyRole API
INFO - PartyRole details: name=NewRole, href=/component/partyRoleManagement/v4/partyRole/123
INFO - Keycloak role NewRole added to component
INFO - === NOTIFICATION PROCESSING COMPLETE (partyRole) ===
```

## Monitoring Benefits

1. **Visibility**: Full visibility into which components have registered listeners
2. **Debugging**: Detailed error messages and request/response logging
3. **Health Monitoring**: Status endpoint and periodic summaries
4. **Audit Trail**: Complete log of all notifications received and processed
5. **Troubleshooting**: Clear identification of registration failures and their causes

## Configuration

The logging level can be controlled via the `LOGGING` environment variable:
- `10` = DEBUG: Shows all details including payloads
- `20` = INFO: Shows key events and summaries
- `30` = WARNING: Shows only warnings and errors

## Endpoints

### Identity Listener Endpoints
- `POST /listener` - Receive notifications (existing)
- `GET /status` - Health check and status information (new)

The status endpoint returns:
```json
{
  "service": "identity-listener-keycloak",
  "status": "running", 
  "endpoints": {
    "/listener": "POST - Receive notifications from APIs",
    "/status": "GET - View service status and health"
  },
  "keycloak_connection": "connected",
  "environment": {
    "KEYCLOAK_BASE": "http://keycloak:8080",
    "KEYCLOAK_REALM": "canvas",
    "KEYCLOAK_USER": "admin"
  }
}
```
