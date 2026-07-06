# Echo Base Development Diary

This document serves as the chronological engineering journal for the Echo Base project.

Unlike `ROADMAP.md`, which tracks implementation status, this document records **what was actually accomplished**, why decisions were made, architectural discoveries, design changes, verification performed, and recommended next steps.

Every meaningful development session should append a new entry to this file.

---

# Development Guidelines

Each entry should include:

- Date
- Summary
- Motivation
- Features Added
- Architecture Decisions
- Files Created / Modified
- Verification
- Outstanding Work
- Next Steps

This document is intended to tell the engineering story of Echo Base from its inception.

---

# 2026-07-05 — Project Inception

## Summary

Echo Base was conceived as a new open-source project focused on building a unified Radio Operations Platform.

Rather than creating another SDR application, the goal is to provide a modern browser-based command center capable of orchestrating radios, SDRs, digital communications, recording, mapping, automation, and future AI-assisted spectrum intelligence.

The overall philosophy is heavily inspired by enterprise observability platforms and network operations centers rather than traditional amateur radio software.

---

## Motivation

Modern radio operators often use numerous independent applications simultaneously.

Examples include:

- SDR software
- ADS-B decoders
- APRS clients
- Winlink
- JS8Call
- WSJT-X
- FLDIGI
- rtl_433
- Weather satellite software
- Recording utilities

Each application performs a specific function but there is currently no unified platform that provides centralized management, visualization, automation, recording, messaging, and system health.

Echo Base aims to become that platform.

---

## Project Name

Selected:

**Echo Base**

The name was chosen because it evokes the idea of a remote communications and monitoring station.

Future consideration may be given to trademark implications if the project grows significantly, but it is currently the working project name.

---

## Initial Vision

Echo Base will function as a Radio Operations Platform capable of managing:

- Software Defined Radios
- Conventional radios
- Digital communications
- Spectrum monitoring
- Recording
- Automation
- Mapping
- Messaging
- Remote receiver sites
- Future AI-assisted analysis

The platform should feel like a professional communications command center.

---

## Initial Technology Decisions

Backend

- Python
- FastAPI
- asyncio
- SQLAlchemy
- SQLite

Frontend

- React
- TypeScript
- Tailwind CSS
- Vite

Deployment

- Linux-first
- systemd
- Native installation
- Future Docker support

---

## Initial Architectural Decisions

Echo Base will be built as a modular service-oriented platform.

Subsystems communicate through:

- REST APIs
- WebSockets
- Internal event bus

Everything should be designed around plugins whenever practical.

Echo Base orchestrates external applications rather than replacing them.

---

## Initial Feature Areas

The first architecture draft identified the following major subsystems:

- Dashboard
- Receiver Manager
- Radio Manager
- Spectrum Intelligence
- Messaging Center
- Digital Modes
- Recording Engine
- Maps
- Automation Engine
- Scheduler
- Alert Engine
- Plugin Manager
- Configuration
- User Management
- AI Layer

These subsystems are expected to evolve independently while sharing a common API.

---

## Documentation Created

Initial project documentation includes:

- README.md
- ARCHITECTURE.md
- ROADMAP.md
- DEVELOPMENT_DIARY.md

These documents should remain synchronized throughout development.

---

## UI Direction

Initial dashboard concepts were created.

The desired interface resembles a communications command center rather than a traditional SDR application.

Desired characteristics include:

- Dark theme
- Real-time updates
- Multiple receiver panels
- Waterfalls
- Spectrum displays
- Messaging center
- Digital mode monitoring
- Recording controls
- Maps
- Alerts
- System health
- Live activity feeds

The interface should be visually impressive while remaining operationally useful.

---

## Plugin Philosophy

Echo Base should expose well-defined plugin interfaces for:

Hardware

- SDRs
- Radios

Software

- Decoders
- Messaging systems
- Mapping
- Recording
- AI modules

Future contributors should be able to extend the platform without modifying the core application.

---

## Long-Term Vision

Echo Base should eventually become an extensible platform capable of supporting:

- Amateur radio
- Aviation monitoring
- Marine monitoring
- Weather
- Emergency communications
- Search & Rescue
- Public events
- Research
- Education
- RF experimentation
- Spectrum intelligence

---

## Verification

Completed:

- GitHub repository created
- Apache 2.0 license selected
- Initial documentation authored
- Project direction established
- Initial dashboard concepts reviewed

No application code has been written at this stage.

---

## Outstanding Work

Remaining work includes:

- Repository scaffolding
- Backend project initialization
- Frontend project initialization
- Configuration system
- Logging
- Service architecture
- Plugin framework
- REST API foundation

---

## Next Milestone

The immediate objective is to establish the project skeleton.

Recommended tasks:

1. Create backend FastAPI project structure.
2. Create React/TypeScript frontend.
3. Define project directory layout.
4. Implement configuration loader.
5. Establish logging framework.
6. Implement health endpoint.
7. Configure WebSocket infrastructure.
8. Build initial dashboard shell.
9. Define plugin interfaces.
10. Commit the initial application framework.

---

## Notes

From the beginning, Echo Base should be treated as a long-term platform rather than a single application.

Architecture decisions should favor extensibility, modularity, maintainability, and automation over rapid feature implementation.

Every subsystem should be designed with future distributed deployments, plugin expansion, and AI-assisted radio intelligence in mind.

The project's guiding principle remains:

> **Echo Base is not another SDR application—it is a Radio Operations Platform.**

---

# 2026-07-05 — Platform Foundation and First Working Walking Skeleton

## Summary

Built Echo Base from an empty repository (documentation only) up
through a working vertical slice: a modular FastAPI backend, a plugin
framework, a real Receiver Manager backed by an RTL-SDR plugin, and a
React/TypeScript/Tailwind dashboard that logs in, shows system health,
streams live events over WebSocket, and controls receivers end to end.
This corresponds to completing Phase 1 (Platform Foundation) and a
meaningful slice of Phase 2 (Receiver Management) from ROADMAP.md.

## Motivation

HANDOFF_PROMPT.md's "Current Development Strategy" prescribes building
in order: scaffolding, backend framework, frontend framework,
configuration, logging, authentication, plugin framework, Receiver
Manager, dashboard. Rather than stop at a bare scaffold, this session
carried that sequence through to a working, testable, demoable slice —
a "walking skeleton" that proves the whole architecture (REST +
WebSocket + event bus + plugin system) actually fits together, rather
than leaving each piece unverified in isolation.

## Features Added

Backend (`backend/`):

- Configuration system: layered YAML + `ECHO_BASE_*` env vars + defaults, via `pydantic-settings` with a custom YAML source.
- Structured logging: console + rotating file handler, optional JSON formatter, plugin-scoped loggers.
- Database: SQLAlchemy 2.0 async + `aiosqlite`, `User` model with role enum, Alembic scaffolding with an initial migration.
- Authentication: bcrypt password hashing, JWT session cookie (also accepted as `Bearer`), role-based dependency guards (administrator/operator/observer/guest), first-run admin bootstrap with a randomly generated password.
- Event bus: asyncio pub/sub with a bounded history buffer, thread-safe `emit()` for plugin code running off the event loop.
- WebSocket infrastructure: `ConnectionManager` fanning event-bus traffic out to `/ws/events`, with cookie/Bearer auth on connect.
- Plugin framework: manifest schema (`manifest.yaml`), `PluginManager` (discovery, dynamic import, enable/disable/reload lifecycle), base interfaces for every plugin category (`Plugin`, `ReceiverPlugin`, `RadioPlugin`, `DecoderPlugin`, `DashboardPlugin`, `AutomationPlugin`).
- Receiver Manager: `ReceiverService` aggregating receiver plugins behind one API, dispatching blocking plugin calls via `asyncio.to_thread`.
- REST API: system (info/health/metrics), auth, users/roles, config (get/update/reload), receivers, plugins, and event history -- all using the standard `{success, data}` / `{success: false, error}` envelope from `docs/REST_API.md`, enforced via centralized FastAPI exception handlers.
- `rtl_sdr` plugin (`plugins/rtl_sdr/`): discovers RTL-SDR hardware via the `rtl_test` CLI tool and models device lifecycle/tuning state (no IQ streaming yet).

Frontend (`frontend/`):

- Vite + React + TypeScript + Tailwind CSS, dark "command center" theme.
- Auth context + protected routes; login page.
- Dashboard shell: sidebar, topbar (live-connection indicator, user/logout), system health widget, live activity feed.
- Receiver Manager UI: list/discover receivers, start/stop, tune, gain, all wired to the real REST API.
- Shared WebSocket event-stream context (one socket for the whole authenticated app, not one per component).

## Architecture Decisions

- **`ReceiverPlugin` lifecycle methods take an explicit `receiver_id`**, refining docs/PLUGIN_API.md's single-device sketch so one plugin instance (e.g. `rtl_sdr`) can manage multiple physical devices, matching README's "Multiple RTL-SDR receivers" goal.
- **Renamed the per-device status method to `device_status`**, keeping the inherited `Plugin.status()` as a no-argument, plugin-level health probe used generically by `GET /api/plugins`. Overriding `status()` with an incompatible signature was caught by a test and is exactly the kind of accidental breakage this split prevents.
- **Standard API envelope enforced centrally** via FastAPI exception handlers (`EchoBaseError`, `HTTPException`, `RequestValidationError`, and a catch-all), so every route -- present and future -- gets consistent `{success, data}` / `{success: false, error: {code, message}}` responses without each handler re-implementing it.
- **Schema creation via `Base.metadata.create_all` on startup, with Alembic scaffolded but not yet the enforced path.** Alembic holds a real, hand-written initial migration and a working async `env.py`, but the running app currently just creates missing tables for a zero-config first run. This is an explicit, temporary tradeoff for a single-table schema; Alembic becomes load-bearing once migrations need to be reviewable.
- **Login cookie's `secure` flag gated on `environment == "production"`, not `!= "development"`.** A `testing` environment run over plain HTTP (as in the test suite) needs the cookie sent; only real production behind TLS should require it.
- **Frontend talks to the same public REST/WebSocket API a third-party client would use** (via a thin `fetch` wrapper unwrapping the envelope), per ARCHITECTURE.md's "no private backend interfaces for the frontend" rule.

## Files Created / Modified

- `backend/` -- entire FastAPI application (see `backend/app/` subpackages: `core`, `db`, `plugins`, `services`, `websocket`, `api`, `schemas`), plus `alembic/`, `tests/`, `requirements*.txt`, `pyproject.toml`.
- `frontend/` -- entire Vite/React/TypeScript application under `src/`.
- `plugins/rtl_sdr/` -- reference receiver plugin (`manifest.yaml`, `plugin.py`, `requirements.txt`).
- `config/config.example.yaml` -- documented configuration template.
- `.gitignore` -- Python/Node/runtime-data ignores.
- `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/PLUGIN_API.md`, `docs/REST_API.md`, `docs/INSTALL.md` -- updated to describe what's actually implemented versus still planned.

## Verification

- `backend`: 12 pytest cases pass (system health/auth-required, login/logout/session, receiver discovery/lifecycle/404, plugin list/enable/disable/404), using an in-process ASGI client and a throwaway mock receiver plugin so hardware-independent behavior is covered without needing real SDR hardware.
- Ran the real server with `uvicorn` (not just the test client) with the actual `rtl_sdr` plugin loaded: confirmed health, login, `/api/auth/me`, `/api/receivers` (correctly empty -- no SDR hardware attached to this machine), `/api/plugins`, `/api/system`, and WebSocket auth (unauthenticated connections rejected, authenticated ones succeed).
- Frontend: `npm install` and `npm run build` (including `tsc -b` type-checking) succeed with zero errors, run inside a Node 22 container via rootless `podman` since Node/npm are not installed on the host.
- Ran the Vite dev server against the real backend through the documented `/api` proxy and exercised the browser-facing flow via curl (serve `index.html`, health, login, session-cookie reuse, authenticated `/api/receivers`) end to end.

## Outstanding Work

- No actual IQ sample streaming from receivers yet (lifecycle/tuning state only).
- No setup wizard; first-run admin bootstrap is a stopgap.
- `/api/system/logs` not implemented.
- SoapySDR and other SDR hardware plugins not started.
- Radio Manager, Recording, Messaging, Automation, Maps, AI: not started (Phases 3+).
- No CI configuration yet.

## Recommended Next Steps

1. Decide on an IQ streaming transport (WebSocket binary frames vs. a dedicated media endpoint) before building real sample streaming -- this affects the Receiver Manager and dashboard waterfall work together.
2. Add Receiver Profiles (frequency/gain/bandwidth/decoder presets) since README and ARCHITECTURE.md both call this out explicitly for Phase 2.
3. Start Phase 3 (Radio Manager / Hamlib integration) once Receiver Manager profiles land, following the same plugin-framework pattern established here.
4. Add CI (lint + `pytest` + frontend `tsc`/`build`) so regressions are caught automatically as the plugin ecosystem grows.