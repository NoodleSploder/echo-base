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
- Platform foundation: backend framework, configuration, logging, database, authentication, plugin framework (Phase 1)
- Frontend framework: React/TypeScript/Tailwind dashboard shell with auth and live updates (Phase 1)
- Draggable/persisted widget-grid dashboard (react-grid-layout), replacing the original fixed sidebar/topbar shell
- CI (backend: ruff + pytest; frontend: eslint + tsc/build)
- Receiver Manager core + a working `rtl_sdr` reference plugin (Phase 2, partial)
- Receiver Profiles (saved frequency/gain presets, apply-to-receiver)
- Unified live IQ capture (`StreamService`): one hardware claim per receiver feeds spectrum FFT, software audio demod (FM/AM), and decoders -- not three competing subprocesses (Phase 2/4, partial)
- Live Spectrum Monitor widget + per-tile Receiver Tiles waterfalls (real FFT data, Phase 4 partial)
- Live audio ("Listen") with squelch/level meter (Phase 2/5, partial)
- First two real decoders, from scratch: APRS (AFSK1200/AX.25) and NOAA Weather Radio SAME, both wired into the dashboard (Phase 5/7, partial)

---

## In Progress

- Richer hardware support beyond `rtl_sdr` (Phase 2)
- Un-mocking remaining dashboard widgets (Digital Modes, Messaging beyond APRS, Recording, wideband Spectrum Overview) as their backend subsystems land

---

## Known Environment Blocks

These aren't abandoned -- they're blocked on resources this development environment doesn't currently have. Revisit when the resource becomes available; see `DEVELOPMENT_DIARY.md` for the entries where each was hit.

- **Phase 3 (Radio Management / Hamlib).** No serial/CAT-capable transceiver is attached here (checked: no `/dev/ttyUSB*`/`/dev/ttyACM*`, no `rigctl`/`rigctld` installed). Every feature built so far has been verified against real attached hardware (an RTL-SDR receive-only dongle); starting Radio Manager without a real rig to test against would break that pattern. Needs: a CAT-capable transceiver (or a rigctld-compatible simulator) connected to whatever machine is doing the work.
- **Real over-the-air decoder verification (APRS, SAME).** Both decoders are proven correct via synthetic encode/decode round-trip tests, but have not decoded a single real packet -- there's no guarantee of an active APRS station or NOAA Weather Radio transmitter in range of whatever antenna is attached here. Needs: real RF activity in range, or a known-good test transmission.
- **Browser-based UI/UX verification.** No display or headless browser is available in this environment, so frontend work (including the entire draggable dashboard grid and all "Listen"/level-meter/squelch UI) is verified via `tsc`/`eslint`/build success and code review, not by looking at or listening to it. Needs: a display or headless browser (e.g. Playwright) available to the development environment.

---

## Remaining

Everything else from Phase 3 onward not listed above as completed/in-progress.

---

# Phase 1 — Platform Foundation

## Backend

Completed

- FastAPI project scaffold (`backend/app`)
- API framework (routers, dependency injection, standard response envelope, centralized exception handling)
- Configuration system (YAML + environment overrides, see `config/config.example.yaml`)
- Logging framework (structured console + rotating file, JSON-capable)
- SQLite integration (SQLAlchemy 2.0 async + Alembic scaffolding)
- Authentication (session-cookie/Bearer JWT, bcrypt password hashing, first-run admin bootstrap)
- User management (CRUD + role-based access: administrator/operator/observer/guest)
- Health monitoring (`/api/system/health`, `/api/system/metrics`)
- REST API foundation (system, auth, users, config, receivers, plugins, events)
- WebSocket infrastructure (internal event bus + `/ws/events` live stream)

Remaining

- `/api/system/logs` (log viewer endpoint)
- OAuth2 / OpenID Connect
- API tokens distinct from session JWTs

---

## Frontend

Completed

- React + TypeScript + Vite application
- Tailwind integration with a dark "command center" theme
- Dashboard framework (routing, protected routes, layout shell)
- Navigation (sidebar with active-section highlighting; future sections marked "coming soon")
- Theme (dark, consistent with the command-center direction from the dev diary)
- WebSocket client (shared event-stream context, auto-reconnect)
- Login flow and system health / live activity widgets
- Notification system (toast stack, distinct from the raw event feed --
  SameAlert/ReceiverStarted/ReceiverStopped surface as dismissible,
  auto-expiring toasts; high-frequency event types like
  AprsPacket/SignalDetected deliberately don't, to avoid toast spam)
- Receiver profile management UI (`ReceiverProfilesPanel`: create/apply/delete
  plus suggested-preset "Add", see the receiver-profiles diary entries)

Remaining

- Accessibility and responsive-layout pass

---

## Configuration

Completed

- YAML configuration (`config/config.yaml`, optional)
- Environment overrides (`ECHO_BASE_*`)
- Secrets (`security.secret_key`, redacted from `GET /api/config`)

Remaining

- Hardware discovery wizard
- Initial setup wizard (first-run currently auto-creates an admin account instead)

---

# Phase 2 — Receiver Management

## SDR Discovery

Completed

- RTL-SDR detection (via `rtl_test`, in the `rtl_sdr` plugin)

Remaining

- SoapySDR detection
- Airspy / SDRplay / HackRF / PlutoSDR / LimeSDR plugins
- Receiver inventory persistence (currently discovered live, not stored)
- USB hot-plug monitoring

---

## Receiver Control

Completed

- Frequency, gain, bandwidth, sample rate (lifecycle state, via REST)
- Live IQ sample streaming (`StreamService`, feeding spectrum/audio/decoders/recording)
- Capture health monitoring (`GET /api/receivers/{id}/capture-health`: worker-thread liveness,
  last-read age, subscriber counts -- surfaced in the UI as a "Capture stalled" badge)

Remaining

- Profiles
- Calibration

---

## Receiver Profiles

Completed

- Built-in "suggested" band presets (FM broadcast, NOAA Weather Radio,
  APRS 2m, Marine VHF ch16, 2m amateur calling, airband guard,
  ADS-B 1090MHz) -- one-click "Add" turns any of them into a real,
  editable/deletable saved profile via the existing create/apply flow.
  All within RTL-SDR tuning range; ADS-B/AIS/HF entries below are
  listed since a preset just means "tune here", not "decode this" --
  actual ADS-B/AIS decoding is still unbuilt (see Remaining).

Remaining

- ADS-B decoding (Mode S/1090MHz -- needs a much higher sample rate
  capture path than the current FM/AM-oriented one; see
  `suggested_profiles.py`'s ADS-B entry, which is spectrum/IQ-only for now)
- AIS decoding (161-162MHz VHF, GMSK)
- Amateur digital modes beyond APRS (see Phase 5)
- Weather satellite presets (APT/Meteor-M2 downlink decoding, Phase 7)
- HF monitoring (outside RTL-SDR's tuning range without an upconverter)
- Spectrum scanning (automated multi-frequency sweep)

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

Completed

- Live waterfall / spectrum displays (real FFT data, `SpectrumMonitorWidget`/`ReceiverTileGridWidget`)
- Signal detection / peak analysis (`SignalDetected` events: noise-floor-relative threshold, bucket+cooldown re-trigger suppression -- see `signal_detection.py`)
- Occupancy analysis (`OccupancyTracker`: per-bin EMA of noise-floor-relative occupancy, pollable via `GET /api/receivers/{id}/occupancy`)
- Signal history (`SignalDetectionRecord` DB table, survives restarts, queryable via `GET /api/receivers/{id}/signal-history` -- no retention/pruning policy yet)

Remaining

- RF heat maps
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

Completed

- APRS position parsing: uncompressed and compressed (base-91) formats
  -- lat/lon/symbol extracted from decoded APRS packets and surfaced
  in the dashboard. Mic-E (the format most real hardware trackers
  actually use) is deliberately not implemented yet -- see
  `aprs_position.py`'s docstring and the diary for why. No map view
  exists yet, only a coordinates readout.
- APRS station persistence (`aprs_stations` table: last known
  position per callsign, survives restarts, queryable via
  `GET /api/aprs/stations`) -- the data layer a map needs, plus a
  compact "known stations" strip in the Messaging Center's APRS tab.
  Still no actual map/tile rendering (see below).

Remaining

- APRS map (station markers/tile rendering on an actual map -- the
  station data itself is now persisted and queryable, see above)
- APRS Mic-E position format (needs real captured packets to verify against, not a from-memory table transcription)
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

Completed

- Core framework: manifest schema, discovery/loading, enable/disable/reload lifecycle, per-plugin config and logger injection (`backend/app/plugins/`)
- Base interfaces for every plugin category (`Plugin`, `ReceiverPlugin`, `RadioPlugin`, `DecoderPlugin`, `DashboardPlugin`, `AutomationPlugin`)

Remaining

- Plugin registry / marketplace, install/uninstall via API
- Hot reload without dropping in-flight operations
- Sandboxed execution

## Hardware Plugins

Completed

- RTL-SDR (`plugins/rtl_sdr/`)

Remaining

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