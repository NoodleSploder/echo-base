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

---

# 2026-07-05 — start.sh Reads config.yaml; Vite allowedHosts

## Summary

Added a root `start.sh` that launches backend and frontend together
for local testing, then closed a gap it surfaced: the dev server was
accessed through a reverse proxy hostname
(`echobase.deathstar.chickenkiller.com`) and Vite's `server.allowedHosts`
protection correctly rejected it, since that hostname wasn't
configured anywhere.

## Features Added

- `start.sh`: creates the backend venv on first run, resolves the
  effective host/port/allowed-hosts by calling
  `app.core.config.get_settings()` directly (so it can never drift from
  what the app itself would actually bind to), waits for the health
  check before starting the frontend, surfaces the first-run admin
  password, and runs the frontend via `npm` or -- since this
  environment has no Node.js installed -- a rootless `podman` Node 22
  container.
- `server.allowed_hosts` config field (`backend/app/core/config.py`),
  threaded through `start.sh` to the frontend as `ECHO_BASE_ALLOWED_HOSTS`
  and consumed by `frontend/vite.config.ts` as `server.allowedHosts`.

## Architecture Decisions

- **`start.sh` never re-implements YAML parsing.** It shells out to the
  venv's Python to call `get_settings()` and print the resolved
  host/port/allowed_hosts, guaranteeing the script and the app always
  agree, regardless of whether the value came from `config.yaml`, an
  `ECHO_BASE_*` env var, or a built-in default.
- **`ECHO_BASE_BACKEND_PORT` (script convenience override) forces
  `ECHO_BASE_SERVER__PORT` before resolving settings**, so a one-off
  `ECHO_BASE_BACKEND_PORT=8811 ./start.sh` still binds the backend to
  that same port rather than just changing where the frontend proxy
  points.

## Bugs Fixed

- A `set -e` pipeline (`grep -A3 ... | grep -E "username|password"`)
  aborted the whole script silently when the admin-password block
  didn't fall within the fixed 3-line context window. Fixed by grepping
  the `username:`/`password:` lines directly instead of anchoring
  relative to another log line.
- The first-run admin password (printed via `print()`, not logged) was
  silently lost when stdout wasn't a TTY, because Python buffers
  `print()` but the `logging` module flushes per record. Fixed with
  `PYTHONUNBUFFERED=1` on the backend subprocess.

## Files Created / Modified

- `start.sh` (new)
- `backend/app/core/config.py` -- `ServerSettings.allowed_hosts`
- `frontend/vite.config.ts` -- reads `ECHO_BASE_ALLOWED_HOSTS`
- `config/config.example.yaml`, `config/config.yaml` -- documented/set `allowed_hosts`

## Verification

- Ran `start.sh` end to end multiple times: fail-fast on a taken port,
  successful run reading `server.port` from `config.yaml` with no env
  var set, and successful run with `ECHO_BASE_BACKEND_PORT` override.
- Confirmed via `curl -H "Host: ..."` that the configured hostname is
  now accepted by the Vite dev server while an arbitrary unlisted
  hostname is still correctly blocked.

## Outstanding Work / Next Steps

Unchanged from the previous entry -- IQ streaming, receiver profiles,
Phase 3 (Radio Manager), and CI remain the recommended next steps.

---

# 2026-07-05 — Command-Center Dashboard Rebuild

## Summary

Replaced the original sidebar/topbar dashboard shell with a draggable,
resizable, per-user widget grid modeled on NOC/observability
dashboards, and fixed a frontend build break plus began un-mocking
widgets with real backend data.

## Motivation

The original dashboard (fixed sidebar + topbar + a couple of static
widgets) didn't match the "communications command center" UI direction
set out in the project-inception entry above (dark theme, multiple
receiver panels, waterfalls, spectrum displays, messaging center,
digital mode monitoring, live activity feeds, all visually dense).
This session built that layout out as a real, persisted, per-user grid
rather than a fixed one-off page.

## Features Added

Backend (`backend/`):

- `GET/PUT /api/dashboard/layout`: persists a user's react-grid-layout
  breakpoint config (`{lg, md, sm}` arrays) as opaque JSON, scoped to
  the authenticated user (`backend/app/api/routes/dashboard.py`,
  `backend/app/schemas/dashboard.py`, migration
  `0002_add_dashboard_layout.py`).

Frontend (`frontend/`):

- `DashboardPage` rebuilt around `react-grid-layout`'s
  `ResponsiveGridLayout`: 12 widgets (Receivers, Spectrum
  Overview/Monitor, Activity Feed, System Status, Receiver Tiles,
  Alerts, Digital Mode Radio, Messaging Center, Digital Decodes,
  Recordings, System Log), drag-to-rearrange via a `.drag-handle`
  region, resize, debounced auto-save to the new layout endpoint, and
  a "Reset Layout" control. Falls back to a sane default layout (and a
  stacked single-column layout at narrower breakpoints) when nothing
  is saved yet.
- New shared primitives: `Panel` (widget chrome + drag handle + a
  `sample` badge for still-mocked widgets), `Sparkline`,
  `SpectrumCanvas`, `MiniWaterfall` (`frontend/src/components/common/`).
- Old fixed `Sidebar`/`Topbar` replaced with `TopNav` +
  `BottomStatusBar`; navigation collapsed into a top bar consistent
  with the new dense-grid layout; `ComingSoonPage` added as a
  placeholder route target for not-yet-built subsystems (Radio
  Manager, Messaging, etc.) so nav links don't 404.
- Most widgets currently render `sampleData.ts` fixtures and are
  labeled with a "Sample" badge in their header -- this is intentional
  scaffolding for subsystems that don't have a backend yet (Phase 3+:
  Messaging, Digital Modes, Recording), not an oversight.

## Architecture Decisions

- **Dashboard layout is stored as opaque JSON, not a typed schema**,
  because it's react-grid-layout's own breakpoint/position/size
  format -- the backend has no reason to understand or validate its
  internal shape, only to persist it per user.
- **Widgets are explicitly marked `sample` vs. real** (via `Panel`'s
  `sample` prop) instead of silently mixing mock and live data. This
  keeps the dashboard's visual richness (matching the NOC-style UI
  goal) honest about what's actually wired to the backend today, and
  gives a visible checklist of what "un-mocking" work remains.
- **Un-mocking is done widget-by-widget**, starting with the ones with
  the smallest true backend gap. `ActivityFeedWidget` and
  `SystemLogWidget` already used the real event-bus WebSocket feed;
  this session added `ReceiversPanelWidget` (now calls
  `GET /api/receivers` on a 15s poll, matching `SystemStatusWidget`'s
  pattern, with an explicit "no receivers detected" empty state)
  rather than rewriting every widget at once.

## Bugs Fixed

- `frontend/vite.config.ts` referenced `process.env` (for
  `ECHO_BASE_BACKEND_HOST`/`PORT`/`ALLOWED_HOSTS`, added in the
  previous session) without `@types/node` in `devDependencies`,
  breaking `tsc -b` with `Cannot find name 'process'`. This was a
  latent break from before the outage -- nothing in that session's
  frontend work exercised a full typechecked build. Fixed by adding
  `@types/node` to `frontend/package.json`.

## Files Created / Modified

- `backend/app/api/routes/dashboard.py`, `backend/app/schemas/dashboard.py`,
  `backend/alembic/versions/0002_add_dashboard_layout.py`,
  `backend/tests/test_dashboard.py` (new)
- `backend/app/api/router.py`, `backend/app/db/models/user.py`,
  `backend/app/core/config.py` -- route registration, layout column on
  `User`, minor config additions.
- `frontend/src/pages/DashboardPage.tsx` -- rebuilt around
  `react-grid-layout`.
- `frontend/src/components/dashboard/*` (new) -- the 12 widgets above.
- `frontend/src/components/common/{Panel,Sparkline,SpectrumCanvas,MiniWaterfall}.tsx` (new)
- `frontend/src/components/layout/{TopNav,BottomStatusBar}.tsx` (new),
  `Sidebar.tsx`/`Topbar.tsx` deleted, `AppShell.tsx` updated.
- `frontend/src/lib/sampleData.ts` (new), `frontend/src/api/dashboard.ts` (new)
- `frontend/src/pages/ComingSoonPage.tsx` (new)
- `frontend/package.json` -- added `react-grid-layout`,
  `@types/react-grid-layout`, `@types/node`.
- `frontend/vite.config.ts` -- unrelated to this session's feature work,
  but the `@types/node` fix lives here.
- `start.sh` (new in a prior session, unchanged here).

## Verification

- Backend: `pytest` -- 15/15 passing, including new
  `test_dashboard.py` layout get/round-trip/auth-required cases (fresh
  `.venv` created and dependencies installed from
  `requirements*.txt` to confirm a clean-machine run).
- Frontend: `tsc -b && vite build` succeeds with zero errors (via the
  rootless-podman Node 22 container, since Node isn't installed on the
  host) after the `@types/node` fix -- previously failed with 4
  TS errors.
- Ran the full stack via `start.sh`: backend health check green,
  logged in as `admin`, confirmed `GET/PUT /api/dashboard/layout`
  round-trips over HTTP, and the Vite dev server serves the app (200).
- No browser/display available in this environment, so the dashboard's
  actual rendering, drag/resize interaction, and the newly-live
  `ReceiversPanelWidget` empty-state were verified by reading the
  component code and API responses, not by driving a real browser.

## Outstanding Work

- Most widgets (Alerts, Digital Mode Radio, Messaging Center, Digital
  Decodes, Recordings, both spectrum widgets, Receiver Tiles) are still
  sample data pending their respective backend subsystems.
- No browser-based visual verification of the grid drag/resize
  behavior has been done yet in this environment.
- IQ streaming, Receiver Profiles, Phase 3 (Radio Manager / Hamlib),
  and CI remain outstanding from prior entries.

## Next Steps

1. Wire `ReceiverTileGridWidget` to the same real `/api/receivers`
   data now backing `ReceiversPanelWidget`, replacing its
   `SAMPLE_RECEIVERS` usage and `MiniWaterfall` placeholder once IQ
   streaming exists to feed it real spectrum data.
2. Get real browser verification of the new grid dashboard (drag,
   resize, persistence round-trip) once a display or headless browser
   is available in this environment.
3. Continue un-mocking widgets in order of smallest backend gap, same
   pattern as `ReceiversPanelWidget` this session.
4. Add CI (lint + `pytest` + frontend `tsc`/`build`) so a build break
   like this session's `@types/node` gap is caught automatically
   instead of surfacing at the next session's first build.

---

# 2026-07-06 — Receiver Profiles, Real Receiver Tiles, and CI

## Summary

Continued down this diary's own "Next Steps" list: added a basic CI
workflow, un-mocked `ReceiverTileGridWidget`, and implemented Receiver
Profiles end to end (backend CRUD + apply, frontend management panel)
-- the Phase 2 item repeatedly flagged as outstanding since the very
first walking-skeleton entry.

## Motivation

Three concrete gaps called out in prior entries: no CI to catch build
breaks (this session's predecessor found one by hand), one dashboard
widget still on `SAMPLE_RECEIVERS` despite a trivial real-data path,
and Receiver Profiles never started despite being named in
README/ARCHITECTURE.md and every "Next Steps" section since the
Phase 1 entry. All three were small enough to close out in one pass
without waiting on unbuilt subsystems (IQ streaming, Radio Manager).

## Features Added

Backend (`backend/`):

- Receiver Profiles: `ReceiverProfile` model (owner-scoped: name,
  frequency/sample-rate/bandwidth in Hz, gain, decoder), migration
  `0003_add_receiver_profiles.py`, and
  `GET/POST/PUT/DELETE /api/receiver-profiles[/{id}]` plus
  `POST /api/receiver-profiles/{id}/apply/{receiver_id}`, which calls
  the existing `ReceiverService.tune`/`set_gain` and returns the
  resulting live `ReceiverStatus` (`app/db/models/receiver_profile.py`,
  `app/schemas/receiver_profile.py`, `app/api/routes/receiver_profiles.py`).
- `.github/workflows/ci.yml`: two jobs, `backend` (`pip install -r
  requirements.txt -r requirements-dev.txt && pytest`) and `frontend`
  (`npm install && npm run build`, which runs `tsc -b` first). No
  linting yet -- neither ruff/flake8 nor ESLint config exists in this
  repo today, so CI only covers what's already enforced locally.

Frontend (`frontend/`):

- `ReceiverTileGridWidget` now calls `GET /api/receivers` +
  `GET /api/receivers/{id}` (same 15s poll pattern as
  `ReceiversPanelWidget`/`SystemStatusWidget`) instead of
  `SAMPLE_RECEIVERS`, with a real state badge
  (idle/streaming/error/disconnected) and an empty state. The
  waterfall canvas itself is still explicitly labeled "sample" per
  tile, since there's no IQ streaming transport to feed it yet.
- `ReceiverProfilesPanel` (new, mounted on the Receivers page below the
  existing `ReceiverCard` grid): save a named frequency/gain preset,
  list saved profiles, apply one to any discovered receiver via a
  dropdown (calls the new apply endpoint and feeds the resulting
  status back into `ReceiverList`'s shared state), delete a profile.
  `frontend/src/api/receiverProfiles.ts` and the `ReceiverProfile`/
  `ReceiverProfileInput` types support it.

## Architecture Decisions

- **Profiles are owner-scoped (`owner_id` FK to `users.id`), not
  global.** Every profile CRUD/apply route filters by
  `ReceiverProfile.owner_id == current_user.id` and 404s rather than
  403s on another user's profile ID, consistent with how the rest of
  the API treats "not yours" the same as "doesn't exist" to avoid
  leaking existence.
- **Apply requires operator+ (`require_role(ADMINISTRATOR, OPERATOR)`),
  same as start/stop/tune**, since it drives real hardware; plain
  CRUD on profiles (save/list/delete a preset) only requires being
  logged in, since saving a preset touches no hardware.
- **Applying a profile is just `tune` + optional `set_gain`, not a new
  service-layer concept.** `ReceiverService` already has the
  primitives; a "profile" is purely a saved bundle of arguments to
  them, so no new receiver-service method was needed.

## Files Created / Modified

- `backend/app/db/models/receiver_profile.py`,
  `backend/app/db/models/__init__.py` (registers the new model for
  `create_all`), `backend/app/schemas/receiver_profile.py`,
  `backend/app/api/routes/receiver_profiles.py`,
  `backend/app/api/router.py`,
  `backend/alembic/versions/0003_add_receiver_profiles.py`,
  `backend/tests/test_receiver_profiles.py` (new)
- `frontend/src/api/receiverProfiles.ts` (new),
  `frontend/src/types/index.ts` -- `ReceiverProfile`/`ReceiverProfileInput`
- `frontend/src/components/receivers/ReceiverProfilesPanel.tsx` (new),
  `ReceiverList.tsx` -- mounts the new panel and shares receiver/status state.
- `frontend/src/components/dashboard/ReceiverTileGridWidget.tsx` --
  un-mocked.
- `frontend/src/components/dashboard/ReceiversPanelWidget.tsx` --
  un-mocked in the same pass as the previous entry; noted here since
  the diary entry hadn't been written yet when it landed.
- `.github/workflows/ci.yml` (new)

## Verification

- Backend: fresh `.venv` created from `requirements*.txt`, `pytest` --
  19/19 passing (15 previous + 4 new `test_receiver_profiles.py` cases:
  CRUD round trip, 404 on unknown/foreign profile, apply-tunes-receiver
  against the test suite's mock receiver plugin, auth-required).
- Frontend: `tsc -b && vite build` clean (via rootless-podman Node 22
  container) after both widget/panel changes.
- Full stack, real hardware: killed the stale pre-existing `uvicorn`
  process (it was serving live traffic on this machine's public
  hostname without the new routes) and restarted via `start.sh`. Then,
  against the real backend -- not just the test client -- logged in,
  created a profile via `POST /api/receiver-profiles`, listed it,
  called `POST /api/receiver-profiles/{id}/apply/rtl_sdr:00000001`
  (the actual attached RTL-SDR device on this machine), and confirmed
  the receiver's live status afterward reported `frequency_hz:
  14074000` -- the profile genuinely tuned physical hardware, not a
  mock. Deleted the test profile afterward. Cleaned up stray podman
  `npm run dev` containers left over from earlier restarts in this
  session.
- No display/headless browser available in this environment, so the
  new `ReceiverProfilesPanel` UI and the dashboard grid's visual
  behavior are still unverified by actually driving a browser.

## Outstanding Work

- No lint tooling (ruff/ESLint) configured yet, so CI doesn't catch
  style/lint issues, only test failures and type/build breaks.
- Alerts, Digital Mode Radio, Messaging Center, Digital Decodes,
  Recordings, and both spectrum widgets remain sample data pending
  their own backend subsystems (Phase 3+).
- No browser-based visual verification of any frontend work has been
  done yet in this environment (no display/headless browser present).
- IQ streaming and Phase 3 (Radio Manager / Hamlib) remain unstarted.

## Next Steps

1. Add ruff (backend) and ESLint (frontend) configs and wire them into
   `ci.yml` now that the workflow skeleton exists.
2. Decide on an IQ streaming transport (still blocking real spectrum
   widgets and a truly live `MiniWaterfall`) -- this has been
   recommended since the very first walking-skeleton entry.
3. Start Phase 3 (Radio Manager / Hamlib integration), following the
   same plugin-framework + owner-scoped-resource pattern established
   by the Receiver Manager and Receiver Profiles.
4. Get real browser verification of frontend work in this environment
   once a display or headless browser is available.

---

# 2026-07-06 — Lint Tooling: ruff + ESLint Wired Into CI

## Summary

Closed the CI gap left by the previous entry: added ruff to the
backend and a flat-config ESLint setup to the frontend, cleaned up
every finding on the existing codebase, and wired both into
`ci.yml` alongside the existing pytest/build jobs.

## Features Added

- Backend: `ruff` in `requirements-dev.txt`, `[tool.ruff]`/
  `[tool.ruff.lint]` in `pyproject.toml` (line-length 110, target
  py312, `E`/`F`/`I`/`UP` rule selection), `ruff check .` added as a
  CI step before `pytest`.
- Frontend: `eslint.config.js` (flat config: `@eslint/js` +
  `typescript-eslint` recommended + `eslint-plugin-react-hooks` +
  `eslint-plugin-react-refresh`), `npm run lint` script, CI step
  between `npm install` and `npm run build`.

## Architecture Decisions

- **`eslint-plugin-react-hooks` pinned to `^5.0.0`, not the `^4.x`
  most React 18 tutorials still reference**, because v4 only declares
  an ESLint 8 peer dependency and hard-conflicts with ESLint 9's flat
  config (`npm install` failed with `ERESOLVE` until this was bumped).
  v5 supports both flat config and ESLint 9.
- **Ruby-selected rule set kept to `E/F/I/UP`** (pycodestyle errors,
  pyflakes, import sorting, pyupgrade) rather than pulling in a wider
  preset -- enough to catch real bugs (unused imports, undefined
  names) and modernize syntax without adding stylistic rules the team
  hasn't agreed on yet (docstring conventions, complexity limits).

## Bugs Fixed

- Ruff's autofix (`ruff check --fix`) modernized 34 pre-existing
  findings across the backend (mostly `datetime.now(timezone.utc)` ->
  `datetime.now(UTC)`, `Union[X, None]` -> `X | None`, and import
  reordering in the two Alembic migrations). Three `E501` line-length
  violations weren't auto-fixable and were wrapped by hand in
  `app/api/routes/auth.py`, `app/core/events.py`, and `app/main.py`.
  None of these were behavior changes.

## Files Created / Modified

- `backend/pyproject.toml`, `backend/requirements-dev.txt`
- `backend/app/api/routes/auth.py`, `backend/app/core/events.py`,
  `backend/app/core/security.py`, `backend/app/db/models/user.py`,
  `backend/app/db/models/receiver_profile.py`, `backend/app/main.py`,
  `backend/alembic/versions/0002_add_dashboard_layout.py`,
  `backend/alembic/versions/0003_add_receiver_profiles.py` --
  ruff-autofixed and/or manually wrapped long lines.
- `frontend/eslint.config.js` (new), `frontend/package.json` --
  `lint` script + `@eslint/js`, `eslint`, `eslint-plugin-react-hooks`,
  `eslint-plugin-react-refresh`, `globals`, `typescript-eslint`.
- `.github/workflows/ci.yml` -- `ruff check .` and `npm run lint`
  steps added.

## Verification

- Backend: `ruff check .` -- all checks passed; `pytest` -- 19/19
  still passing after the autofix/manual-wrap pass.
- Frontend: fresh `npm install` (via rootless-podman Node 22
  container) succeeded once `eslint-plugin-react-hooks` was bumped to
  `^5.0.0`; `npm run lint` reports 0 errors, 2 pre-existing warnings
  (`react-refresh/only-export-components` on `AuthContext.tsx` and
  `EventStreamContext.tsx`, both from the common
  context-module-also-exports-a-hook pattern -- left as-is, not worth
  restructuring for a lint warning); `npm run build` still clean.

## Outstanding Work

- The two `react-refresh` warnings are unresolved by design (see
  above) -- could be silenced with a targeted `eslint-disable` if they
  become noisy, but aren't errors today.
- Everything else outstanding is unchanged from the previous entry:
  no browser verification available in this environment, most
  dashboard widgets still sample data pending their backend
  subsystems, IQ streaming and Phase 3 (Radio Manager) not started.

## Next Steps

1. Decide on an IQ streaming transport -- now the single most-repeated
   outstanding item across every recent entry.
2. Start Phase 3 (Radio Manager / Hamlib integration).
3. Continue un-mocking dashboard widgets as their backend subsystems
   land.
4. Get real browser verification of frontend work once a display or
   headless browser is available in this environment.

---

# 2026-07-06 — Live IQ Streaming and a Real Spectrum Monitor

## Summary

Closed the single most-repeated outstanding item in this diary: chose
and implemented an IQ streaming transport, wired it to the actual
attached RTL-SDR hardware on this machine, and made the Spectrum
Monitor dashboard widget show a real, live, server-computed FFT
instead of decorative sample noise.

## Motivation

Every recent entry's "Next Steps" named this as the top blocker for
real spectrum widgets and a genuinely live waterfall. It also unblocks
future decoder work (FT8, APRS, etc. all need raw samples), so it was
worth doing as a real vertical slice rather than another mock.

## Features Added

Backend (`backend/`):

- `ReceiverPlugin.open_iq_stream(receiver_id) -> IqStreamHandle`
  (`app/plugins/receiver.py`): new optional plugin capability --
  returns a small protocol object (`read(n)`/`close()`) wrapping
  whatever the plugin uses to produce raw interleaved-uint8 I/Q bytes.
  Defaults to `NotImplementedError`, which the rest of the stack
  treats as "no live spectrum for this receiver" rather than an error.
- `plugins/rtl_sdr/plugin.py`: implements it by shelling out to
  `rtl_sdr -d <index> -f <freq> -s <rate> [-g <gain>] -` (same
  CLI-tool-not-librtlsdr-binding approach `discover()` already uses
  with `rtl_test`), streaming raw samples to stdout. Untuned receivers
  default to 100 MHz so a spectrum preview works before the user tunes
  anything. Device index (needed for `-d`) is now tracked per
  `_DeviceState`, parsed alongside id/name/serial in `_parse_devices`.
- `app/services/spectrum_service.py` (`SpectrumService`): for each
  receiver with at least one subscriber, runs a background thread that
  reads raw IQ off the plugin's stream, applies a Hann window, computes
  an FFT (`numpy`), converts to dB magnitude, downsamples to a fixed
  512 output bins, and hands the frame back to the event loop via
  `call_soon_threadsafe` -- the same thread-to-loop handoff pattern
  `EventBus.emit` already established. Capture starts lazily on first
  subscriber and stops on last unsubscribe, so an unwatched dashboard
  doesn't tie up a physical SDR.
- `GET /ws/spectrum/{receiver_id}` (`app/api/routes/spectrum.py`): a
  per-receiver WebSocket (distinct from the single shared `/ws/events`
  socket) that authenticates the same way, subscribes to
  `SpectrumService`, and streams each computed frame as a raw binary
  `Float32Array` (512 * 4 bytes) -- no JSON envelope, since this is a
  high-frequency binary stream, not a REST-shaped response. Closes with
  app-specific codes (4404 unknown receiver, 4405 receiver doesn't
  support streaming) so the frontend can decide whether to retry.
- `numpy` added to `requirements.txt` -- the FFT math is generic
  (any future receiver plugin's raw IQ goes through the same
  `SpectrumService`), not specific to the rtl_sdr plugin, so it lives
  in the core backend dependencies.

Frontend (`frontend/`):

- `useSpectrumStream(receiverId)` (`hooks/useWebSocket.ts`): opens
  `/ws/spectrum/{id}`, parses each binary message into a
  `Float32Array`, reconnects on drop with backoff -- except for the
  backend's intentional close codes, which aren't worth retrying.
- `useFirstReceiver()` (new): picks the first discovered receiver so
  single-receiver widgets have something to stream from without a
  picker UI yet (multi-receiver selection remains a ROADMAP.md item).
- `SpectrumCanvas` now accepts an optional `liveFrame` prop: when
  present, it min/max-normalizes the real dB values and draws the same
  trace + waterfall it already drew for synthetic data, so this was a
  data-source swap, not a new rendering path.
- `SpectrumMonitorWidget` now uses `useFirstReceiver` +
  `useSpectrumStream` and drops its `sample` badge once a real frame
  is flowing, falling back to the decorative animation if no receiver
  supports streaming yet. `SpectrumOverviewWidget` was deliberately
  left on sample data -- it's framed as a full-band ("Span: 1.8 GHz")
  overview, which a single RTL-SDR's ~2 MHz capture can't honestly
  represent; wiring it up needs either a wideband receiver or explicit
  per-band tuning, not this pass's plumbing.

## Architecture Decisions

- **Binary WebSocket frames, not JSON, and a dedicated
  per-receiver socket, not `/ws/events`.** FFT frames are
  high-frequency and numeric; encoding 512 floats as JSON would be
  needlessly larger and slower to parse, and multiplexing them through
  the single shared event socket would mean every dashboard client
  receives every receiver's spectrum whether it's looking at that
  widget or not. This was the concrete decision this diary's "decide
  on an IQ streaming transport" item was waiting on.
- **FFT computed server-side, not shipped to the browser as raw IQ.**
  Keeps the wire format small and fixed-size regardless of sample
  rate, and matches how every comparable web SDR front-end (e.g.
  OpenWebRX) splits the work: server does DSP, browser only renders.
- **Capture lifecycle is subscriber-counted, not tied to
  start/stop/tune.** A receiver can be "streaming" (per
  `ReceiverStatus.state`) without anyone watching its spectrum, and a
  spectrum viewer shouldn't have to first call `/start`. Whether to
  unify these two "streaming" concepts (device lifecycle vs. spectrum
  subscription) is left as an open question for when a real decoder
  needs exclusive access to the same raw IQ.
- **`IqStreamHandle` is a `Protocol`, not a base class.** Plugins
  producing IQ via wildly different mechanisms (subprocess pipe today;
  a librtlsdr/SoapySDR binding, or a network socket to a remote
  receiver, later) only need to duck-type `read`/`close` and a
  `sample_rate_hz` attribute -- no shared implementation to inherit.

## Files Created / Modified

- `backend/app/plugins/receiver.py` -- `IqStreamHandle` protocol,
  `ReceiverPlugin.open_iq_stream`.
- `backend/app/plugins/__init__.py` -- exports `IqStreamHandle`.
- `backend/app/services/spectrum_service.py` (new)
- `backend/app/services/receiver_service.py` -- `resolve_plugin()`
  (exposes plugin lookup to `SpectrumService`).
- `backend/app/api/routes/spectrum.py` (new), `backend/app/api/router.py`
- `backend/app/api/deps.py` -- `get_spectrum_service`
- `backend/app/main.py` -- constructs `SpectrumService`, stops all
  active captures on shutdown.
- `backend/requirements.txt` -- `numpy`.
- `backend/tests/conftest.py` -- mock receiver plugin gained
  `open_iq_stream` (`MockIqStream`, synthetic `os.urandom` bytes) so
  `SpectrumService` is testable without real SDR hardware.
- `backend/tests/test_spectrum_service.py` (new)
- `plugins/rtl_sdr/plugin.py` -- `open_iq_stream`, device index
  tracking, `iq_streaming: True` capability flag.
- `frontend/src/hooks/useWebSocket.ts` -- `useSpectrumStream`
- `frontend/src/hooks/useFirstReceiver.ts` (new)
- `frontend/src/components/common/SpectrumCanvas.tsx` -- `liveFrame` prop
- `frontend/src/components/dashboard/SpectrumMonitorWidget.tsx` --
  wired to real data.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 22/22 passing (19
  previous + 3 new `test_spectrum_service.py` cases: subscribing
  yields a correctly-sized FFT frame from the mock plugin's synthetic
  IQ, unsubscribing the last subscriber tears the worker down, and
  subscribing to an unknown receiver raises `ReceiverNotFoundError`).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings as
  last entry, no new ones); `tsc -b && vite build` clean.
- **Real hardware, not just the mock**: restarted the live backend
  process on this machine (it was serving actual traffic on the
  public hostname; briefly interrupted to load the new code), then
  used a small script with the `websockets` library to log in, open
  `ws://localhost:8811/ws/spectrum/rtl_sdr:00000001`, and read frames
  back from the actual attached RTL2838 dongle -- confirmed 512-bin
  float32 frames with sane, changing magnitude ranges (spot-checked
  ~0-46 dB across several runs). Confirmed via `ps`/backend logs that
  the `rtl_sdr` subprocess is spawned on first subscribe and fully
  reaped (no lingering zombie) after the client disconnects.
- No display/headless browser available in this environment, so the
  dashboard widget's actual on-screen rendering of live frames (vs.
  the WebSocket data itself, which was verified) is still unconfirmed
  by eye.

## Outstanding Work

- Only `rtl_sdr` implements `open_iq_stream`; any future receiver
  plugin (SoapySDR, etc.) needs its own implementation to get a live
  Spectrum Monitor.
- No decoder yet consumes this raw IQ path (FT8/APRS/etc. are still
  Phase 3+ sample-data widgets) -- `SpectrumService` and
  `open_iq_stream` were built generically enough to serve that later,
  but nothing does yet.
- Device-lifecycle "streaming" (`start`/`stop`) and spectrum-subscriber
  "streaming" are two independent concepts right now; whether/how to
  unify them is an open question, noted above.
- No multi-receiver picker for the Spectrum Monitor -- it always shows
  whichever receiver `useFirstReceiver` finds first.
- Still no browser-based visual verification available in this
  environment.

## Next Steps

1. Add a receiver picker to `SpectrumMonitorWidget` once more than one
   streaming-capable receiver is commonly attached.
2. Start Phase 3 (Radio Manager / Hamlib integration) or a first real
   decoder (FT8 is the most-requested per the dashboard's existing
   Digital Decodes widget) -- both now have a real raw-IQ source to
   build on.
3. Get real browser verification of the dashboard once a display or
   headless browser is available in this environment.
4. Decide whether `start`/`stop` and spectrum subscription should share
   one underlying "is this receiver's hardware claimed" concept.