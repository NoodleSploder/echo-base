# Echo Base Architecture

> **Version:** 0.1.0
>
> Echo Base is an open-source Radio Operations Platform designed to unify SDRs, transceivers, digital mode software, messaging systems, recording, automation, and spectrum intelligence into a single browser-based command center.

---

# Philosophy

Echo Base is **not** another SDR application.

Echo Base is an orchestration platform.

Its responsibility is to coordinate, monitor, automate, and visualize an entire radio ecosystem.

Rather than replacing existing open-source radio software, Echo Base integrates with best-in-class projects and presents them through a common API and unified web interface.

Examples include:

- SoapySDR
- rtl_tcp
- Hamlib
- rigctld
- dump1090 / readsb
- rtl_433
- Dire Wolf
- Pat (Winlink)
- JS8Call
- WSJT-X
- FLDIGI
- SatDump
- GNU Radio
- OpenWebRX (future integration)

Echo Base becomes the control plane.

---

# Design Principles

Echo Base should always strive for:

- Modular architecture
- Service-oriented design
- API-first development
- Plugin extensibility
- Hardware abstraction
- Live updates
- Zero page refreshes
- Automation-first workflows
- Linux-first deployment
- Open standards whenever possible

---

# High-Level Architecture

```
                     Browser Dashboard
                            │
                  REST + WebSocket API
                            │
                     FastAPI Backend
                            │
      ┌─────────────────────┼─────────────────────┐
      │                     │                     │
 Configuration        Event Bus          Authentication
      │                     │                     │
      ├─────────────────────┼─────────────────────┤
      │                     │                     │
 Receiver Manager     Radio Manager      Automation Engine
      │                     │                     │
      ├─────────────────────┼─────────────────────┤
      │                     │                     │
 Plugin Manager      Recording Engine    Scheduler
      │                     │                     │
      └─────────────────────┼─────────────────────┘
                            │
                External Applications
                            │
        SDRs • Radios • Digital Decoders
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- asyncio
- SQLAlchemy
- Alembic
- Pydantic
- WebSockets

---

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

Future additions may include:

- React Flow
- Leaflet
- Plotly
- xterm.js
- Monaco Editor

---

## Database

Initial:

- SQLite

Future:

- PostgreSQL

The application should support either without code changes.

---

# Core Components

---

## Dashboard

Provides the primary operations center.

Responsibilities:

- Receiver status
- Radio status
- Live spectrum
- Maps
- Messaging
- Alerts
- Recordings
- Health monitoring
- Active decoders

---

## Receiver Manager

Responsible for SDR hardware.

Supports:

- RTL-SDR
- Airspy
- SDRplay
- HackRF
- PlutoSDR
- LimeSDR
- SoapySDR devices

Responsibilities:

- Discovery
- Configuration
- Assignment
- Calibration
- Gain
- Frequency
- Bandwidth
- Streaming

---

## Radio Manager

Controls traditional radios.

Supports:

- Hamlib
- rigctld
- CAT interfaces
- USB Serial
- Network radios

Responsibilities:

- Frequency
- Mode
- Power
- PTT
- Memories
- Status

Every supported radio is implemented through an adapter.

---

## Plugin Manager

Echo Base is plugin-driven.

Plugins provide:

- SDR drivers
- Radio drivers
- Digital decoders
- Maps
- Dashboards
- AI modules
- Automation actions

Plugins should be installable without modifying the core platform.

---

## Digital Modes

Coordinates external applications.

Examples:

- APRS
- Packet
- Winlink
- JS8
- FT8
- FT4
- WSPR
- SSTV
- DMR
- P25
- M17
- NXDN
- FreeDV

Echo Base launches, monitors, configures, and visualizes these applications.

---

## Messaging Center

Unified communications view.

Supports:

- APRS
- Winlink
- JS8
- Packet
- Future messaging systems

Messages become searchable historical events.

---

## Spectrum Intelligence

Provides RF awareness.

Features:

- Waterfalls
- Spectrum displays
- Occupancy
- Heat maps
- Peak detection
- Signal history
- Recording triggers

---

## Recording Engine

Supports:

- IQ recording
- Audio recording
- Waterfall snapshots
- Triggered recording
- Scheduled recording
- Event recording

Recordings become searchable assets.

---

## Maps

Displays:

- APRS stations
- ADS-B aircraft
- AIS vessels
- Satellites
- Receiver locations
- Propagation
- Weather

---

## Automation Engine

Automation should become a major capability.

Examples:

IF

- Callsign detected
- Aircraft enters airspace
- Satellite rises
- APRS message received
- Signal exceeds threshold
- Decoder recognizes event

THEN

- Record
- Notify
- Execute script
- Send webhook
- Transmit message
- Launch decoder

---

## Alert Engine

Supports:

- Email
- Discord
- Matrix
- MQTT
- Webhooks

Future:

- SMS
- Signal
- Telegram

---

## Scheduler

Responsible for:

- Satellite passes
- Scheduled recordings
- Band scans
- Periodic health checks
- Maintenance tasks

---

## AI Layer (Future)

Potential capabilities:

- Signal classification
- Unknown signal detection
- Occupancy analysis
- Decoder recommendations
- Recording summaries
- Automatic tagging
- Natural language search

---

# Receiver Profiles

Receivers should be configured using reusable profiles.

Examples:

- ADS-B
- Airband
- NOAA
- APRS
- Marine AIS
- Amateur VHF
- Amateur UHF
- HF Monitoring
- Weather Satellites
- Spectrum Scanner

Profiles define:

- Frequency
- Bandwidth
- Gain
- Decoder
- Recording policy

---

# Plugin Architecture

Every hardware integration should expose a common interface.

Example:

```python
class ReceiverPlugin:

    def discover(self):
        ...

    def start(self):
        ...

    def stop(self):
        ...

    def tune(self, frequency):
        ...

    def status(self):
        ...
```

The same philosophy applies to:

- Radios
- Decoders
- Messaging
- Maps
- AI

---

# REST API

Everything should be controllable through REST.

Examples:

```
GET    /api/receivers

POST   /api/receiver/{id}/start

POST   /api/receiver/{id}/stop

POST   /api/receiver/{id}/tune

GET    /api/radios

GET    /api/messages

GET    /api/recordings

POST   /api/recordings/start

POST   /api/automation

GET    /api/system
```

The frontend should consume the same public API available to third-party applications.

---

# Event Bus

Internal communication should be event-driven.

Examples:

```
ReceiverStarted

ReceiverStopped

SignalDetected

RecordingStarted

RecordingFinished

MessageReceived

AircraftDetected

AISContact

SatellitePass

AlertGenerated
```

Everything publishes events.

Everything subscribes to events.

---

# Configuration

Configuration should support:

- YAML
- Environment variables
- Secrets
- Multiple configuration files

Future:

Database-backed configuration.

---

# Logging

Every subsystem should produce structured logs.

Logs should include:

- Timestamp
- Component
- Severity
- Event
- Metadata

Future support:

- OpenTelemetry
- Loki
- Elasticsearch

---

# Security

Authentication:

- Local accounts
- OAuth2
- OpenID Connect (future)

Authorization:

- Role-based permissions

Examples:

- Administrator
- Operator
- Observer
- Guest

---

# Scalability

Echo Base should support:

- One SDR on a Raspberry Pi

through

- Multiple radio servers
- Remote SDR clusters
- Distributed receiver sites
- Enterprise deployments

No architectural assumptions should limit future horizontal scaling.

---

# Future Vision

Echo Base should become the open-source platform for radio operations.

Ultimately supporting:

- SDR management
- Radio control
- Digital communications
- Satellite operations
- Aviation
- Marine
- Emergency communications
- Weather
- Search and rescue
- Public events
- Education
- Research
- RF intelligence
- Automation
- AI-assisted spectrum analysis

The long-term objective is to provide a single, extensible platform capable of managing every aspect of modern radio operations through an elegant, browser-based command center.