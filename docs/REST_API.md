# Echo Base REST API

> **Version:** 0.1.0 (Draft)

The Echo Base REST API provides a consistent, versioned interface for controlling every subsystem within the platform.

The REST API is considered the **public contract** between the backend, frontend, plugins, automation engine, CLI tools, and third-party applications.

Every feature exposed by the web interface should also be accessible through the REST API.

**Implementation status:** System, Authentication, Users/Roles,
Configuration, Receivers, Plugins, and the live Events stream (this
page's respective sections) are implemented in `backend/app/api/routes/`.
Radios, Digital Modes, Messaging, Recording, Maps, Spectrum, Automation,
Alerts, Scheduler, and AI are documented below as the target design but
not yet implemented -- see `ROADMAP.md` for sequencing.

---

# Design Goals

The API is designed to be:

- RESTful
- Versioned
- Consistent
- Self-documenting
- API-first
- Plugin extensible
- Secure
- Easy to automate

---

# Base URL

```
/api
```

Future versions may support:

```
/api/v1
/api/v2
```

---

# Authentication

Initially:

- Local user accounts
- Session cookies

Future:

- OAuth2
- OpenID Connect
- API Tokens
- JWT

---

# Standard Response Format

Successful responses:

```json
{
    "success": true,
    "data": {}
}
```

Errors:

```json
{
    "success": false,
    "error": {
        "code": "RECEIVER_NOT_FOUND",
        "message": "Receiver does not exist."
    }
}
```

---

# System

## System Information

```
GET /api/system
```

Returns:

- Version
- Hostname
- Platform
- Uptime
- CPU
- Memory
- Disk
- Services

---

## Health Check

```
GET /api/system/health
```

---

## Metrics

```
GET /api/system/metrics
```

---

## Logs

```
GET /api/system/logs
```

---

# Configuration

## Get Configuration

```
GET /api/config
```

---

## Update Configuration

```
PUT /api/config
```

---

## Reload Configuration

```
POST /api/config/reload
```

---

# Users

## List Users

```
GET /api/users
```

---

## Create User

```
POST /api/users
```

---

## Update User

```
PUT /api/users/{id}
```

---

## Delete User

```
DELETE /api/users/{id}
```

---

## Roles

```
GET /api/roles
```

---

# Receivers

## List Receivers

```
GET /api/receivers
```

---

## Receiver Details

```
GET /api/receivers/{id}
```

---

## Discover Receivers

```
POST /api/receivers/discover
```

---

## Start Receiver

```
POST /api/receivers/{id}/start
```

---

## Stop Receiver

```
POST /api/receivers/{id}/stop
```

---

## Restart Receiver

```
POST /api/receivers/{id}/restart
```

---

## Tune Receiver

```
POST /api/receivers/{id}/tune
```

Example:

```json
{
    "frequency": 144390000
}
```

---

## Set Gain

```
POST /api/receivers/{id}/gain
```

---

## Set Sample Rate

```
POST /api/receivers/{id}/sample-rate
```

---

## Set Bandwidth

```
POST /api/receivers/{id}/bandwidth
```

---

## Assign Profile

```
POST /api/receivers/{id}/profile
```

---

## Receiver Statistics

```
GET /api/receivers/{id}/statistics
```

---

## Receiver Waterfall

```
GET /api/receivers/{id}/waterfall
```

---

## Receiver Spectrum

```
GET /api/receivers/{id}/spectrum
```

---

# Radios

## List Radios

```
GET /api/radios
```

---

## Radio Details

```
GET /api/radios/{id}
```

---

## Connect

```
POST /api/radios/{id}/connect
```

---

## Disconnect

```
POST /api/radios/{id}/disconnect
```

---

## Set Frequency

```
POST /api/radios/{id}/frequency
```

---

## Set Mode

```
POST /api/radios/{id}/mode
```

---

## PTT

```
POST /api/radios/{id}/ptt
```

---

## Memories

```
GET /api/radios/{id}/memories
```

---

# Digital Modes

## List Decoders

```
GET /api/decoders
```

---

## Start Decoder

```
POST /api/decoders/{id}/start
```

---

## Stop Decoder

```
POST /api/decoders/{id}/stop
```

---

## Decoder Statistics

```
GET /api/decoders/{id}/statistics
```

---

## Decoder Configuration

```
PUT /api/decoders/{id}/config
```

---

# Messaging

## Messages

```
GET /api/messages
```

---

## Message Details

```
GET /api/messages/{id}
```

---

## Send Message

```
POST /api/messages
```

---

## APRS

```
GET /api/messages/aprs
```

---

## Winlink

```
GET /api/messages/winlink
```

---

## JS8

```
GET /api/messages/js8
```

---

# Recording

## List Recordings

```
GET /api/recordings
```

---

## Start Recording

```
POST /api/recordings/start
```

---

## Stop Recording

```
POST /api/recordings/stop
```

---

## Scheduled Recordings

```
GET /api/recordings/scheduled
```

---

## Download Recording

```
GET /api/recordings/{id}/download
```

---

## Delete Recording

```
DELETE /api/recordings/{id}
```

---

# Maps

## Aircraft

```
GET /api/maps/adsb
```

---

## AIS

```
GET /api/maps/ais
```

---

## APRS

```
GET /api/maps/aprs
```

---

## Satellites

```
GET /api/maps/satellites
```

---

## Receivers

```
GET /api/maps/receivers
```

---

# Spectrum

## Live Spectrum

```
GET /api/spectrum/live
```

---

## Occupancy

```
GET /api/spectrum/occupancy
```

---

## Waterfalls

```
GET /api/spectrum/waterfalls
```

---

## Signals

```
GET /api/spectrum/signals
```

---

# Automation

## Rules

```
GET /api/automation/rules
```

---

## Create Rule

```
POST /api/automation/rules
```

---

## Update Rule

```
PUT /api/automation/rules/{id}
```

---

## Delete Rule

```
DELETE /api/automation/rules/{id}
```

---

## Execute Rule

```
POST /api/automation/rules/{id}/execute
```

---

# Alerts

## List Alerts

```
GET /api/alerts
```

---

## Alert History

```
GET /api/alerts/history
```

---

## Acknowledge Alert

```
POST /api/alerts/{id}/ack
```

---

# Scheduler

## Jobs

```
GET /api/scheduler/jobs
```

---

## Create Job

```
POST /api/scheduler/jobs
```

---

## Delete Job

```
DELETE /api/scheduler/jobs/{id}
```

---

# Plugins

## Installed Plugins

```
GET /api/plugins
```

---

## Plugin Details

```
GET /api/plugins/{id}
```

---

## Install Plugin

```
POST /api/plugins/install
```

---

## Uninstall Plugin

```
DELETE /api/plugins/{id}
```

---

## Enable Plugin

```
POST /api/plugins/{id}/enable
```

---

## Disable Plugin

```
POST /api/plugins/{id}/disable
```

---

## Reload Plugin

```
POST /api/plugins/{id}/reload
```

---

# Events

## Live Event Stream

```
GET /api/events
```

Returns:

- Receiver events
- Recording events
- Messages
- Alerts
- Automation
- System health

---

# AI (Future)

## Analyze Recording

```
POST /api/ai/analyze
```

---

## Classify Signal

```
POST /api/ai/classify
```

---

## Search

```
POST /api/ai/search
```

Natural language examples:

> "Show all APRS traffic from yesterday."

> "Find every transmission on 146.520 MHz."

> "Show aircraft within 50 miles."

---

# API Conventions

## HTTP Methods

| Method | Purpose |
|----------|---------|
| GET | Retrieve data |
| POST | Create or execute |
| PUT | Replace |
| PATCH | Partial update |
| DELETE | Remove |

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Error |

---

# API Principles

The Echo Base API follows several core principles:

- Every subsystem is controllable through the API.
- The web UI uses the same public API as external clients.
- APIs should be stable and backward compatible whenever possible.
- Resources should use predictable URLs and HTTP semantics.
- Long-running operations should return job identifiers and expose progress.
- Live data should use WebSockets whenever practical instead of polling.

---

# Future Expansion

Future API capabilities may include:

- GraphQL
- gRPC
- Plugin-defined REST endpoints
- OpenAPI client generation
- Remote cluster management
- Federation between Echo Base servers
- Streaming APIs
- External automation SDKs

---

# Philosophy

The REST API is the foundation of Echo Base.

Every capability within the platform should be accessible through documented, stable, and well-designed APIs, enabling automation, integrations, custom dashboards, mobile applications, and future distributed deployments.
```