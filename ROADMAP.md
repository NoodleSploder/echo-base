# Echo Base Roadmap

> **Project Status:** Early Development
>
> Echo Base is an open-source Radio Operations Platform designed to unify SDRs, transceivers, digital communications, spectrum intelligence, automation, and recording into a single browser-based command center.

This roadmap is intentionally high-level.

It is **not** a changelog.

Detailed implementation history belongs in `DEVELOPMENT_DIARY.md`.

---

# Vision

Echo Base will become the central command platform for modern radio operations.

Long-term goals include:

- SDR management
- Radio control
- Digital communications
- Messaging
- Spectrum intelligence
- Recording
- Automation
- Mapping
- AI-assisted signal analysis
- Distributed radio networks

---

# Current Status

## Completed

- Initial project vision
- Repository created
- Licensing established
- README
- Architecture planning

---

## In Progress

- Project framework
- Backend architecture
- Frontend architecture
- Core service model

---

## Remaining

Everything else.

---

# Phase 1 — Platform Foundation

## Backend

Completed

- None

Remaining

- FastAPI project
- API framework
- Configuration system
- Logging framework
- SQLite integration
- Authentication
- User management
- Health monitoring
- REST API foundation
- WebSocket infrastructure

---

## Frontend

Completed

- UI concepts

Remaining

- React application
- Tailwind integration
- Dashboard framework
- Navigation
- Theme
- WebSocket client
- Notification system

---

## Configuration

Remaining

- YAML configuration
- Environment overrides
- Secrets
- Hardware discovery
- Initial setup wizard

---

# Phase 2 — Receiver Management

## SDR Discovery

Remaining

- RTL-SDR detection
- SoapySDR detection
- Receiver inventory
- USB monitoring

---

## Receiver Control

Remaining

- Frequency
- Gain
- Bandwidth
- Sample rate
- Profiles
- Calibration
- Health monitoring

---

## Receiver Profiles

Remaining

- ADS-B
- Airband
- APRS
- NOAA
- AIS
- Amateur
- Weather satellites
- HF monitoring
- Spectrum scanning

---

# Phase 3 — Radio Management

## Hamlib Integration

Remaining

- rigctld support
- CAT interfaces
- USB Serial
- Network radios

---

## Radio Control

Remaining

- Frequency
- Mode
- Memories
- PTT
- Audio routing
- Status monitoring

---

## Radio Profiles

Remaining

- HF
- VHF
- UHF
- Satellite
- APRS
- Packet

---

# Phase 4 — Spectrum Intelligence

Remaining

- Live waterfall
- Spectrum displays
- Occupancy analysis
- Signal history
- RF heat maps
- Signal detection
- Peak analysis
- Receiver comparison

---

# Phase 5 — Digital Communications

## Messaging

Remaining

- APRS
- Winlink
- JS8
- Packet

---

## Digital Modes

Remaining

- FT8
- FT4
- WSPR
- SSTV
- RTTY
- DMR
- P25
- NXDN
- YSF
- D-STAR
- M17
- FreeDV

---

# Phase 6 — Aviation & Marine

## Aviation

Remaining

- ADS-B
- UAT
- ACARS
- VDL2

---

## Marine

Remaining

- AIS
- Marine VHF

---

# Phase 7 — Weather & Satellite

## Weather

Remaining

- NOAA Weather Radio
- SAME Alerts
- NOAA APT
- Meteor-M2

---

## Satellite

Remaining

- Pass prediction
- Automatic recording
- Tracking
- Scheduling

---

# Phase 8 — Recording

Remaining

- Audio recording
- IQ recording
- Waterfall recording
- Scheduled recording
- Triggered recording
- Replay
- Recording management

---

# Phase 9 — Mapping

Remaining

- APRS map
- ADS-B map
- AIS map
- Receiver map
- Propagation
- Satellite map

---

# Phase 10 — Automation

Remaining

- Rules engine
- Scheduled tasks
- Triggered workflows
- Webhooks
- MQTT
- External scripts

Example automation:

IF

- Callsign detected

THEN

- Record transmission
- Notify operator
- Send webhook

---

# Phase 11 — Alerting

Remaining

- Email
- Discord
- Matrix
- MQTT
- Webhooks

Future

- SMS
- Signal
- Telegram

---

# Phase 12 — Plugin Framework

Remaining

## Hardware Plugins

- RTL-SDR
- Airspy
- SDRplay
- HackRF
- PlutoSDR
- LimeSDR

---

## Radio Plugins

- Hamlib
- CAT
- Vendor APIs

---

## Decoder Plugins

- dump1090
- rtl_433
- Dire Wolf
- JS8Call
- Pat
- WSJT-X
- FLDIGI
- SatDump

---

## Dashboard Plugins

- Widgets
- Panels
- Maps
- Analytics

---

# Phase 13 — Distributed Operations

Remaining

- Remote receivers
- Multi-server deployments
- Cluster management
- Receiver sharing
- Distributed recording
- Central event bus

---

# Phase 14 — Intelligence

Remaining

- Signal classification
- Occupancy analysis
- Decoder recommendations
- AI summaries
- Natural language search
- Historical analytics

---

# Phase 15 — Installer & Packaging

Remaining

## Installation

- Linux installer
- Dependency installer
- Service creation
- Hardware detection
- Initial configuration

---

## Packaging

- Debian packages
- RPM packages
- Arch PKGBUILD
- Docker
- Docker Compose

---

# Phase 16 — Documentation

Remaining

- Installation guide
- Administrator guide
- User guide
- Plugin development guide
- REST API
- WebSocket API
- Architecture diagrams
- Developer documentation

---

# Future Ideas

Potential future capabilities include:

- Mobile applications
- Native desktop client
- SDR recording clusters
- Mesh networking integration
- LoRa support
- Meshtastic integration
- Emergency operations dashboard
- Incident management
- Search & rescue tooling
- Remote station management
- HF propagation prediction
- Antenna management
- Rotor control
- Automatic band planning
- AI-assisted signal identification
- AI-assisted automation generation
- SDR simulation mode
- Public receiver sharing
- Multi-user collaboration
- Role-based operations center

---

# Development Philosophy

Echo Base will prioritize:

- Clean architecture
- Modular services
- Plugin extensibility
- Hardware abstraction
- Open APIs
- Excellent documentation
- Long-term maintainability

The objective is not simply to build another SDR application, but to create the definitive open-source platform for modern radio operations.