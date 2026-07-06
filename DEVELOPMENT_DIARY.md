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

---

# 2026-07-06 — Receiver Picker and Live Audio Listening

## Summary

Two follow-ups from the previous entry's "Next Steps": added a
receiver picker to the Spectrum Monitor widget, and -- the bigger
piece -- a full live-audio path (`AudioService` + `/ws/audio`) so a
receiver can actually be listened to in the browser, not just watched
as a spectrum. Verified against the real attached RTL-SDR: audible-
strength demodulated FM audio, not synthetic data.

## Motivation

Multi-receiver support was an explicit next step. Live audio wasn't
directly named, but it was the obvious next real capability once IQ
streaming existed (previous entry): a "Radio Operations Platform" that
can show you a spectrum but not let you listen to it is missing the
single most basic operator workflow, and `rtl_fm` (already alongside
`rtl_sdr`/`rtl_test`) made it a small addition on top of the
subprocess-streaming pattern `open_iq_stream` already established.

## Features Added

Backend (`backend/`):

- `ReceiverPlugin.open_audio_stream(receiver_id, mode="fm") ->
  AudioStreamHandle` (`app/plugins/receiver.py`): same optional-capability
  shape as `open_iq_stream` (a `Protocol` with `read`/`close`/
  `sample_rate_hz`), but for demodulated mono PCM16 instead of raw I/Q.
- `plugins/rtl_sdr/plugin.py`: implements it via `rtl_fm -d <index> -f
  <freq> -M <mode> -s 200000 -r 48000 [-g <gain>] -`, mirroring
  `open_iq_stream`'s use of `rtl_sdr`. The subprocess-wrapper class
  (`_RtlSdrProcessStream`, renamed from `_RtlSdrIqStream`) is now
  shared by both, since "read a subprocess's stdout until closed" is
  identical for I/Q bytes and PCM bytes. Added `audio_streaming: True`
  to the plugin's capability flags.
- `app/services/audio_service.py` (`AudioService`): structurally the
  same as `SpectrumService` (per-`(receiver_id, mode)` background
  thread, lazy start on first subscriber, stop on last, thread-to-loop
  handoff via `call_soon_threadsafe`) but with no signal processing --
  the plugin already demodulated the audio, so this just re-chunks
  bytes onto subscriber queues.
- `GET /ws/audio/{receiver_id}?mode=fm` (`app/api/routes/audio.py`):
  binary PCM16 chunks, same auth/close-code conventions as
  `/ws/spectrum`. `mode` is validated against an allow-list
  (`fm`/`wbfm`/`am`/`usb`/`lsb`/`raw`) before being passed to the
  plugin, since it flows straight into subprocess arguments.

Frontend (`frontend/`):

- `useAudioPlayer(receiverId, mode, enabled)` (new hook): opens
  `/ws/audio/{id}`, decodes each PCM16 chunk to float, and schedules it
  on a single `AudioContext` back-to-back against a running
  `nextStartTime` cursor -- what keeps ~50ms chunks arriving
  separately over the wire sounding gapless instead of choppy.
- `ReceiverCard` gained a mode selector (FM/AM/USB/LSB) and a
  Listen/Connecting/Listening toggle, shown only when
  `receiver.capabilities.audio_streaming` is true.
- `useReceiverPicker` (renamed from `useFirstReceiver`, same file
  renamed to match): now returns the full receiver list plus a
  selection setter instead of always picking index 0.
  `SpectrumMonitorWidget` shows a `<select>` when more than one
  receiver is present; with only one, it behaves as before.

## Architecture Decisions

- **`_RtlSdrProcessStream` unified rather than duplicated** for audio:
  once the second use case (audio) needed the exact same "spawn a CLI
  tool, read its stdout, terminate on close" wrapper as the first (IQ),
  keeping two copies would just be accidental duplication with no
  behavioral difference.
- **Audio capture is keyed by `(receiver_id, mode)`, not just
  `receiver_id`.** Unlike the spectrum socket (one FFT makes sense per
  receiver), a receiver could plausibly be listened to in different
  demod modes by different observers (e.g. one client on USB for SSB
  voice, another on AM for the same frequency's data mode); keying by
  the pair means switching mode in the UI starts a fresh capture rather
  than fighting over a shared one.
- **Mode validated against an allow-list before reaching the plugin**,
  since `Query` params reach `open_audio_stream` unfiltered otherwise
  and (in the rtl_sdr plugin) get placed directly into subprocess
  `argv`. `subprocess.Popen` without `shell=True` isn't injectable, but
  an arbitrary string there is still an easy way to make `rtl_fm` fail
  in confusing ways -- validating up front gives a clean 4400 instead.

## Files Created / Modified

- `backend/app/plugins/receiver.py` -- `AudioStreamHandle` protocol,
  `ReceiverPlugin.open_audio_stream`.
- `backend/app/plugins/__init__.py` -- exports `AudioStreamHandle`.
- `backend/app/services/audio_service.py` (new)
- `backend/app/api/routes/audio.py` (new), `backend/app/api/router.py`
- `backend/app/api/deps.py` -- `get_audio_service`
- `backend/app/main.py` -- constructs `AudioService`, stops it on shutdown.
- `backend/tests/conftest.py` -- mock plugin gained `open_audio_stream`
  (reuses `MockIqStream`).
- `backend/tests/test_audio_service.py` (new)
- `plugins/rtl_sdr/plugin.py` -- `open_audio_stream`,
  `_RtlSdrProcessStream` rename, `audio_streaming` capability flag.
- `frontend/src/hooks/useAudioPlayer.ts` (new)
- `frontend/src/components/receivers/ReceiverCard.tsx` -- mode
  selector + Listen toggle.
- `frontend/src/hooks/useReceiverPicker.ts` (renamed from
  `useFirstReceiver.ts`) -- returns full list + selection setter.
- `frontend/src/components/dashboard/SpectrumMonitorWidget.tsx` --
  receiver `<select>` when multiple receivers are present.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 25/25 passing (22
  previous + 3 new `test_audio_service.py` cases: subscribe yields a
  non-empty PCM chunk from the mock plugin, last-unsubscribe tears the
  worker down, unknown receiver raises `ReceiverNotFoundError`).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend again (briefly
  interrupting its actual public-hostname traffic), then used a small
  `websockets`-based script to log in and read raw chunks from
  `ws://localhost:8811/ws/audio/rtl_sdr:00000001?mode=fm` against the
  real attached RTL2838 dongle. Chunks had RMS ~5100-5300 (of a
  possible 32768 max) with wide min/max swings -- clearly demodulated
  signal, not silence or noise-floor static. Confirmed via backend
  logs and `pgrep` that the `rtl_fm` subprocess is spawned on
  subscribe and fully gone after the client disconnects, same
  lazy-lifecycle behavior verified for `rtl_sdr`/spectrum previously.
- No display/headless browser in this environment, so the actual
  in-browser audio playback (`useAudioPlayer`'s `AudioContext`
  scheduling) and the new receiver-picker `<select>` are unverified by
  eye/ear -- only the underlying WebSocket data and build/lint/tests
  are confirmed.

## Outstanding Work

- Only `rtl_sdr` implements `open_audio_stream`; future receiver
  plugins need their own implementation for Listen to work.
- No volume control, mute, or visual level meter on the Listen UI --
  just a bare toggle and mode select.
- `AudioContext` creation happens in a `useEffect` triggered by a
  click, not directly in the click handler; this is fine in
  Chrome/Firefox but Safari's stricter autoplay-gesture linking hasn't
  been tested (no browser available here).
- Still no browser-based visual/audible verification in this
  environment.

## Next Steps

1. Verify actual audio playback and the receiver picker in a real
   browser once one is available.
2. Start Phase 3 (Radio Manager / Hamlib integration) or a first real
   decoder (FT8/APRS) -- both spectrum and audio raw-data paths now
   exist to build on.
3. Add a level meter / mute control to the Listen UI.
4. Decide whether `start`/`stop`, spectrum subscription, and now audio
   subscription should share one underlying "is this receiver's
   hardware claimed" concept -- three independent "streaming" notions
   on one receiver is starting to accumulate.

---

# 2026-07-06 — Unified IQ Capture: One Hardware Claim, Not Two

## Summary

Resolved the design question from the previous entry -- specifically
the concrete half of it, the actual bug: spectrum and audio each
opened their own subprocess (`rtl_sdr`, `rtl_fm`) against the same
physical dongle, so watching the Spectrum Monitor and hitting Listen
on the same receiver at the same time raced for exclusive USB access.
Replaced `SpectrumService` + `AudioService` with one `StreamService`
that opens a single `open_iq_stream` per receiver and derives *both*
the FFT and demodulated audio from those same samples in software.
Verified on real hardware that spectrum and audio now genuinely run
concurrently against one receiver with only one subprocess alive.

## Motivation

This was flagged as unresolved risk in both of the last two entries,
not just a tidiness complaint: `rtl_sdr` (used by spectrum) and
`rtl_fm` (used by audio) each try to open the same USB device
exclusively. Two independent subprocesses per receiver meant the
second one to start would fail silently (logged and swallowed by the
worker's `except Exception` -- the user would just see "Connecting..."
forever with no explanation). Fixing it meant giving up two
independent, mode-flexible demod processes in favor of one shared
capture and a real, if limited, software demodulator.

## Features Added

Backend (`backend/`):

- `app/services/dsp.py` (new): `fm_demodulate`/`am_demodulate` --
  quadrature phase-difference FM demod and magnitude AM demod, each a
  crude boxcar decimate (mean-pool, not a real FIR/IIR filter) down to
  48kHz, then per-chunk AGC (normalize to a fixed target peak) before
  quantizing to PCM16. Deliberately simple DSP: intelligible voice
  audio, not broadcast-quality -- SSB (USB/LSB) demod needs a proper
  Hilbert-transform phasing method and was left out rather than faked.
- `app/services/stream_service.py` (new, replaces
  `spectrum_service.py` + `audio_service.py`): one `_ReceiverCapture`
  per receiver, opening exactly one `open_iq_stream`. Each read is fed
  to the FFT path *and* to every currently-subscribed audio mode's
  demodulator -- so N spectrum viewers and M audio listeners (in
  possibly different modes) on one receiver still share one hardware
  claim. Capture starts when the first subscriber of either kind
  arrives and stops when the last of either kind leaves.
  `subscribe_spectrum`/`unsubscribe_spectrum` and
  `subscribe_audio`/`unsubscribe_audio` replace the two services'
  separate APIs.
- `ReceiverPlugin.open_audio_stream` and `AudioStreamHandle` removed
  entirely from the plugin interface (`app/plugins/receiver.py`) --
  audio is now a generic capability of anything that streams IQ, not
  something each plugin implements separately.
- `plugins/rtl_sdr/plugin.py`: `open_audio_stream`/`rtl_fm` subprocess
  removed; `audio_streaming` capability flag removed (subsumed by
  `iq_streaming`, since audio now comes free with it). Default IQ
  sample rate lowered from 2.048 MHz to 240 kHz -- a deliberate
  spectrum-span-for-decimation-simplicity tradeoff, since 240kHz/5 is
  exactly 48kHz (the audio output rate), so the common case needs no
  fractional resampling. Still adjustable via the existing
  `set_sample_rate` API; audio decimation recalculates
  (`round(sample_rate_hz / 48000)`) whatever rate is actually set.
- `/ws/audio/{id}?mode=` now validates against
  `dsp.DEMODULATORS` (`fm`, `am`) instead of a hardcoded allow-list
  that included unimplemented `rtl_fm` modes (`wbfm`/`usb`/`lsb`/`raw`).

Frontend (`frontend/`):

- `ReceiverCard`'s Listen UI now checks `capabilities.iq_streaming`
  instead of a separate `audio_streaming` flag, and its mode dropdown
  is trimmed to `["fm", "am"]` to match what the backend can actually
  demodulate.

## Architecture Decisions

- **One capture serves both features rather than two specialized
  ones.** The alternative (a mutex/lease so only one of
  spectrum/audio could run at a time on a given receiver) would have
  "fixed" the crash but made the platform *less* capable -- an
  operator legitimately wants to watch the waterfall while listening.
  Deriving both from one IQ stream in software is strictly better once
  the DSP is acceptable, which FM/AM (unlike SSB) are simple enough for.
- **Software demod chosen over process-per-mode**, even though it
  means writing (simple) DSP instead of shelling out to a
  battle-tested tool. `rtl_fm` can't share its input stream with
  `rtl_sdr` -- there's no way to keep the "just shell out" approach
  and also share one hardware claim, so this was the one place in the
  project so far where reimplementing instead of wrapping a CLI tool
  was the only option that solved the actual problem.
- **240kHz default sample rate is a real behavior change, not free.**
  The Spectrum Monitor's span narrows from ~2MHz to 240kHz by default.
  This was accepted deliberately: a wide spectrum overview was never
  wired to real data anyway (`SpectrumOverviewWidget` stays sample-only
  per the entry that built it), and 240kHz is still enough span for
  the per-receiver Spectrum Monitor's actual use case (watching a
  channel you're tuned near), while being the cleanest possible ratio
  to 48kHz audio.
- **`_ReceiverCapture.is_idle()` checks both subscriber collections**,
  so the capture is only torn down when *neither* spectrum nor any
  audio mode has a subscriber left -- getting this wrong (e.g. tearing
  down on spectrum's last unsubscribe while audio listeners remain)
  would have silently killed someone's audio to fix someone else's
  disconnect.

## Files Created / Modified

- `backend/app/services/dsp.py` (new), `backend/app/services/stream_service.py`
  (new) -- replace `spectrum_service.py`/`audio_service.py` (deleted).
- `backend/app/plugins/receiver.py`, `backend/app/plugins/__init__.py`
  -- removed `AudioStreamHandle`/`open_audio_stream`.
- `backend/app/main.py`, `backend/app/api/deps.py` -- `StreamService`
  replaces the two removed services.
- `backend/app/api/routes/spectrum.py`, `backend/app/api/routes/audio.py`
  -- delegate to `StreamService`; audio route validates modes against
  `dsp.DEMODULATORS`.
- `backend/tests/conftest.py` -- mock plugin's `open_audio_stream`
  removed (no longer part of the interface).
- `backend/tests/test_stream_service.py` (new, replaces
  `test_spectrum_service.py` + `test_audio_service.py`).
- `plugins/rtl_sdr/plugin.py` -- `open_audio_stream` removed, default
  sample rate 240kHz, `_RtlSdrProcessStream` reverted to
  `_RtlSdrIqStream` (only one subprocess kind now, so the shared-name
  generalization from the previous entry was no longer needed).
- `frontend/src/components/receivers/ReceiverCard.tsx` -- capability
  check and mode list updated.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 25/25 passing, including
  a new `test_spectrum_and_audio_share_one_capture` that asserts
  exactly one `_ReceiverCapture` exists while both a spectrum and an
  audio subscriber are attached to the same mock receiver, and that
  it survives the spectrum subscriber leaving while the audio
  subscriber remains.
- Frontend: `npm run lint` clean (same 2 pre-existing warnings);
  `tsc -b && vite build` clean.
- **Real hardware, the actual regression test**: restarted the live
  backend, then ran a script that opens `/ws/spectrum/...` and
  `/ws/audio/...?mode=fm` *concurrently* against the same physical
  RTL2838 dongle (`asyncio.gather`, not sequential) -- exactly the
  scenario that used to race. Both streamed real data simultaneously
  (spectrum peaks ~26-27dB, audio RMS ~8500-9200). Confirmed via `ps`
  that only one `rtl_sdr` subprocess existed the whole time and no
  `rtl_fm` process ever appeared. Also incidentally verified
  multi-client sharing: a real external dashboard connection was
  already subscribed to spectrum when the test script connected, and
  the test's audio subscription joined the same running capture
  without spawning a new one (no second "Opened IQ stream" log line).
- No display/headless browser in this environment, so actual in-browser
  audio quality (does the FM/AM demod sound acceptable, does switching
  modes in the UI work smoothly) remains unverified by ear.

## Outstanding Work

- SSB (USB/LSB) demod is not implemented -- would need a proper
  Hilbert-transform phasing demodulator, not a small addition like
  FM/AM were.
- The decimation filter is a boxcar mean, not a real low-pass FIR --
  adequate for narrowband voice, would alias more on wider/noisier
  signals. Worth revisiting if audio quality complaints show up once
  someone can actually listen.
- The smaller half of the original design question remains open:
  `ReceiverStatus.state` (idle/streaming, toggled by `start`/`stop`)
  still doesn't reflect whether a capture is actually running --
  spectrum/audio subscription works regardless of whether `start` was
  ever called. Whether `state` should become derived from
  `StreamService` rather than a separate manual flag is still an open
  question, just no longer a correctness bug.
- Still no browser-based visual/audible verification in this
  environment.

## Next Steps

1. Get real browser/audio verification once available in this
   environment.
2. Decide whether `ReceiverStatus.state` should be derived from
   `StreamService`'s active captures instead of toggled independently
   by `start`/`stop`.
3. Start Phase 3 (Radio Manager / Hamlib integration) or a first real
   decoder (FT8/APRS) on top of the now-unified IQ path.
4. Consider a real low-pass FIR before decimation if boxcar-filter
   audio quality turns out to be a problem in practice.

---

# 2026-07-06 — Receiver Status Reflects Real Capture Activity

## Summary

Closed the remaining half of the design question from the last two
entries: `ReceiverStatus.state` was a manual flag toggled by
`start()`/`stop()` that had no idea whether IQ was actually flowing.
The REST layer now reports `"streaming"` whenever `StreamService` has
a live capture for that receiver -- from a spectrum viewer, an audio
listener, or both -- regardless of whether anyone ever called
`/start`. Verified against the real receiver: `idle` -> `streaming` ->
`idle` tracked a spectrum WebSocket's connect/disconnect with no
`/start` call in between.

## Motivation

The previous entry fixed the actual bug (two subprocesses racing for
one dongle) but left the cosmetic half open: an operator could open
the Spectrum Monitor, see real data, and the receiver's own status
badge would still say "idle" because `start()` was never called. That
is actively misleading for something calling itself an operations
platform -- a status field that doesn't reflect the thing it claims to
describe is worse than not having the field.

## Features Added

- `StreamService.is_active(receiver_id) -> bool`
  (`app/services/stream_service.py`): whether a capture currently
  exists for a receiver, i.e. whether IQ is genuinely being read from
  hardware.
- `app/api/routes/receivers.py`: new `_status_response()` helper used
  by every route that returns a `ReceiverStatusSchema` (status, start,
  stop, tune, gain, bandwidth, sample-rate) -- upgrades a plugin-reported
  `"idle"` to `"streaming"` when `StreamService.is_active()` is true.
  Only overrides `"idle"`; a plugin-reported `"error"` or
  `"disconnected"` is left alone, since those describe conditions no
  amount of spectrum-watching should paper over.
  `app/api/routes/receiver_profiles.py`'s `apply` endpoint reuses the
  same helper for consistency.

## Architecture Decisions

- **Merged at the API layer, not inside `ReceiverService`.**
  `ReceiverService` is constructed before `StreamService` in
  `main.py`'s lifespan (`StreamService` depends on it for plugin
  lookup), so giving `ReceiverService` a reference back to
  `StreamService` would be circular. Doing the merge once, in the
  route layer, avoids that entirely and keeps both services ignorant
  of each other beyond the existing `resolve_plugin` call.
  `_status_response()` was pulled out as a shared helper specifically
  so this logic lives in exactly one place rather than being
  copy-pasted across six routes.
- **Only `"idle"` is upgraded, not any other state.** The point is
  "don't lie about whether hardware is idle when it demonstrably
  isn't" -- it is not "let spectrum-watching mask real errors."

## Files Created / Modified

- `backend/app/services/stream_service.py` -- `is_active()`
- `backend/app/api/routes/receivers.py` -- `_status_response()` helper,
  `stream_service` dependency added to every status-returning route.
- `backend/app/api/routes/receiver_profiles.py` -- `apply` reuses the
  shared helper instead of building its own `ReceiverStatusSchema`.
- `backend/tests/test_receivers.py` -- new
  `test_status_reflects_real_capture_without_start`.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 26/26 passing (25
  previous + 1 new test asserting `GET /api/receivers/mock:0` reports
  `idle` before subscribing, `streaming` while a spectrum subscriber
  is attached with no `/start` call, and `idle` again after
  unsubscribing).
- Frontend: unaffected by this change (no frontend edits); `npm run
  lint` and `tsc -b && vite build` re-confirmed clean anyway.
- **Real hardware**: restarted the live backend, then scripted
  `GET /api/receivers/rtl_sdr:00000001` before, during, and after a
  spectrum WebSocket connection (never calling `/start`). Output:
  `idle` -> `streaming` -> `idle`, matching the mock-based test
  exactly.

## Outstanding Work

- `start()`/`stop()` on rtl_sdr remain pure status-flag toggles with
  no hardware effect of their own -- they're now one of two ways
  `state` can say "streaming" (the other being real capture activity),
  which is a bit of an odd pairing but not incorrect. Whether `start`
  should be deprecated/removed now that subscribing already
  auto-starts a capture is an open question, not urgent.
- Same DSP/SSB/browser-verification gaps as the previous entry.

## Next Steps

1. Consider whether `start`/`stop` still pull their weight now that
   spectrum/audio subscription auto-starts a capture regardless.
2. Start Phase 3 (Radio Manager / Hamlib integration) or a first real
   decoder (FT8/APRS) on the unified IQ path.
3. Get real browser/audio verification once available in this
   environment.

---

# 2026-07-06 — Audio Level Meter and Squelch

## Summary

Closed the "Add a level meter / mute control to the Listen UI" item
flagged as outstanding since the audio-listening entry. `ReceiverCard`
now shows a live RMS level bar while listening and a squelch slider
that mutes playback below a threshold -- computed entirely client-side
from the PCM16 chunks already flowing over `/ws/audio`, no backend
changes needed.

## Motivation

Live audio without any level feedback or squelch is hard to use in
practice -- there's no way to tell if a channel is quiet-but-connected
versus dead, and there's no way to avoid constant static/noise between
transmissions on a simplex channel. Both are standard baseline
features on any real scanner/radio, and both turned out to be pure
client-side signal processing on data already being received, not a
new capability the backend needed to provide.

## Features Added

- `useAudioPlayer` (`frontend/src/hooks/useAudioPlayer.ts`) now takes
  a `squelch` (0-1 RMS threshold) argument and returns `level` in
  addition to `connected`. Every incoming PCM16 chunk's RMS is
  computed client-side; chunks below `squelch` update the level meter
  but are not scheduled for playback (silently skipped rather than
  played at zero volume, so the `AudioContext` scheduling cursor
  doesn't drift from real time waiting on gaps).
- `ReceiverCard` gained a level meter (a width-animated bar, amber
  "squelched" label when below threshold) and a squelch range slider,
  shown only while `listening` is on.

## Architecture Decisions

- **Squelch and level computation live entirely in the browser, not
  the backend.** The backend already streams every PCM sample
  regardless of level -- there's no bandwidth or CPU reason to push
  squelch logic server-side, and keeping it client-side means the
  threshold is instantly adjustable (a slider drag) with no round
  trip, and per-listener (two people watching the same receiver could
  in principle want different squelch levels, though the UI doesn't
  expose per-listener anything else either).
- **`squelch` is read via a ref inside the WebSocket effect, not a
  `useEffect` dependency.** Reconnecting the socket every time the
  user drags the slider would be wasteful and would audibly glitch
  playback; the same ref-for-frequently-changing-value pattern
  `SpectrumCanvas`'s `liveFrame` prop already uses.
- **Squelched chunks are dropped, not scheduled silent.** Scheduling a
  silent `AudioBufferSourceNode` still advances `nextStartTime` by the
  chunk's duration, which is harmless either way here since chunks
  arrive at a roughly constant cadence -- but dropping the chunk
  entirely also skips the (tiny but nonzero) cost of building the
  `AudioBuffer` and scheduling it, for chunks nobody will hear anyway.

## Files Created / Modified

- `frontend/src/hooks/useAudioPlayer.ts` -- `squelch` param, `level`
  return value, per-chunk RMS computation.
- `frontend/src/components/receivers/ReceiverCard.tsx` -- level meter
  + squelch slider UI.

## Verification

- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- Backend unaffected (no backend files touched this entry); `ruff
  check .` and `pytest` (26/26) re-confirmed clean anyway.
- **Not verified by ear/eye**: this entry's actual behavior (does the
  meter track real audio level, does squelch audibly gate static)
  can only be confirmed by running the app in a real browser with
  sound, which remains unavailable in this environment. The
  `chunkRms`/squelch-gating logic was verified by reading it, not by
  observing it work -- flagged here rather than glossed over.

## Outstanding Work

- Same as prior entries: no display/headless browser available, so
  this feature -- more than most, since it's inherently about audible
  behavior -- is unverified beyond code review and type-checking.
- No persistence of squelch/mode preference per receiver; resets on
  page reload.

## Next Steps

1. Get real browser/audio verification once available in this
   environment -- overdue across several entries now.
2. Start Phase 3 (Radio Manager / Hamlib integration) or a first real
   decoder (FT8/APRS) on the unified IQ path.
3. Consider whether `start`/`stop` still pull their weight now that
   spectrum/audio subscription auto-starts a capture regardless.

---

# 2026-07-06 — First Real Decoder: APRS (AFSK1200/AX.25)

## Summary

Built Echo Base's first actual digital-mode decoder: a from-scratch
Bell 202 AFSK1200 demodulator and AX.25 frame parser, running on the
same unified IQ capture spectrum/audio already share. Enabling "Decode
APRS" on a receiver runs FM-demodulated audio through the decoder;
valid packets are emitted as `AprsPacket` events on the existing event
bus, so the Activity Feed, System Log, and (now) the Messaging
Center's APRS tab all show real decoded traffic automatically, no new
frontend plumbing beyond the toggle button itself. Correctness is
proven by a synthetic encode-then-decode round-trip test, since real
APRS reception depends on RF conditions this environment doesn't
control.

## Motivation

This was the next step named in the last two entries: "start Phase 3
or a first real decoder" on top of the unified IQ path. APRS (AFSK1200
over FM) was chosen over FT8 because it's a genuinely tractable
from-scratch implementation -- AFSK demod plus HDLC framing is well
within reach; FT8's LDPC decoding and multi-second sync search is a
much larger undertaking better suited to wrapping an existing decoder
than reimplementing.

## Features Added

Backend (`backend/`):

- `app/services/decoders/ax25.py`: AX.25 address encode/decode, FCS
  (CRC-16/X-25) computation and verification, frame parsing
  (destination/source/digipeater path/control/PID/info).
- `app/services/decoders/afsk.py` (`Afsk1200Decoder`): correlates
  audio against 1200Hz/2200Hz tones over a sliding one-bit-period
  window to get a continuous tone-dominance signal; NRZI-decodes bits
  by comparing tone polarity at consecutive bit centers (a transition
  is a 0-bit, no transition is a 1-bit); brute-forces a handful of
  bit-phase offsets per buffer (real bit-period start isn't known in
  advance) and self-rejects wrong ones via HDLC bit-stuffing (6
  consecutive 1-bits can't occur in real destuffed data, so garbage
  phase-offsets essentially never produce a valid flag+FCS).
- `dsp.py`: `fm_demodulate` split into `fm_discriminator` (raw float
  audio, pre-AGC/quantization) + a thin PCM16 wrapper, since the AFSK
  decoder needs the actual waveform, not a volume-normalized copy.
- `StreamService`/`_ReceiverCapture`: `enable_aprs`/`disable_aprs`,
  same lazy lifecycle and `is_idle()` accounting as spectrum/audio
  subscribers (a receiver with only APRS decoding enabled still counts
  as "in use" and keeps the capture alive). Decoded frames are handed
  to `EventBus.emit("AprsPacket", ...)` rather than a dedicated
  WebSocket -- there's no reason to build a fourth channel when
  `/ws/events` already exists and already fans out to every dashboard
  widget that cares about "things happened."
- `POST /api/receivers/{id}/aprs/start` / `/aprs/stop`
  (`app/api/routes/receivers.py`): toggles decoding for a receiver.

Frontend (`frontend/`):

- `ReceiverCard` gained a "Decode APRS" toggle (next to Listen).
- `MessagingCenterWidget`'s APRS tab now shows real `AprsPacket` events
  (filtered from the same event stream `ActivityFeedWidget`/
  `SystemLogWidget` already consume) when any exist, falling back to
  sample data otherwise -- same un-mocking pattern as
  `ReceiversPanelWidget` earlier.

## Architecture Decisions

- **Decoded packets go through the existing EventBus, not a new
  per-receiver WebSocket.** Spectrum and audio needed dedicated binary
  channels because they're high-frequency numeric streams; APRS
  packets are sparse, structured, and exactly the kind of thing
  `/ws/events` already exists for. Reusing it means three dashboard
  widgets got real APRS data for the cost of one filter (`event.type
  === "AprsPacket"`), not three new integrations.
- **Correctness proven by a synthetic round-trip test
  (`test_afsk_decoder.py`), not live reception.** A from-scratch modem
  implementation is exactly the kind of code that's easy to get
  subtly wrong (bit order, NRZI polarity, stuffing edge cases) in ways
  that only show up as "never decodes anything" -- which looks
  identical to "correctly decoding, but no APRS traffic is in range."
  Encoding a known packet to audio and asserting the decoder recovers
  it exactly is the only way to actually distinguish those two cases
  in an environment that can't guarantee real RF activity.
- **No clock-recovery PLL -- fixed samples-per-bit, brute-forced
  phase.** A real implementation (e.g. direwolf) continuously tracks
  the transmitter's bit clock via a PLL to handle long frames and
  clock drift. Given 1200 baud and typical APRS packet durations
  (~200-300ms), a fixed nominal bit period is accurate enough that
  drift never accumulates to a full bit's worth of error within one
  packet -- a deliberate scope cut, not an oversight, and called out
  as a real limitation below.
- **APRS decoding is a capture-level toggle (enable/disable), not a
  per-connection WebSocket subscription** like spectrum/audio.
  Decoded output isn't per-client (everyone sees the same event bus),
  so there's no reason to ref-count "how many people are watching
  APRS" the way spectrum/audio ref-count actual data subscribers --
  just whether decoding is on for that receiver.

## Files Created / Modified

- `backend/app/services/decoders/__init__.py`,
  `backend/app/services/decoders/ax25.py`,
  `backend/app/services/decoders/afsk.py` (all new)
- `backend/app/services/dsp.py` -- `fm_discriminator` extracted from
  `fm_demodulate`.
- `backend/app/services/stream_service.py` -- `enable_aprs`/
  `disable_aprs`, `_decode_aprs`, `EventBus` now a constructor
  dependency.
- `backend/app/main.py` -- `StreamService(receiver_service, event_bus)`.
- `backend/app/api/routes/receivers.py` -- `aprs/start`, `aprs/stop`.
- `backend/tests/test_afsk_decoder.py` (new) -- synthetic round-trip
  test with a self-contained test-only AFSK1200 encoder.
- `backend/tests/test_stream_service.py` -- APRS enable/disable
  lifecycle tests, including sharing a capture with a spectrum
  subscriber.
- `frontend/src/api/receivers.ts` -- `startAprsDecoding`/`stopAprsDecoding`.
- `frontend/src/components/receivers/ReceiverCard.tsx` -- toggle button.
- `frontend/src/components/dashboard/MessagingCenterWidget.tsx` --
  real APRS data when available.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 30/30 passing, including
  `test_afsk_round_trip_recovers_known_packet` (encodes a known AX.25
  UI frame -- `APRS>N0CALL:>Test packet 12345` -- as an AFSK1200
  waveform, feeds it to `Afsk1200Decoder`, and asserts the decoded
  destination/source/info match exactly) and the new APRS
  enable/disable/shared-capture lifecycle tests.
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, tuned the actual
  RTL2838 dongle to 144.390 MHz (the standard North American APRS
  frequency), enabled APRS decoding via the real REST endpoint, and
  listened on `/ws/events` for 20 seconds. Zero packets decoded --
  expected and honestly reported, not a bug: there's no way to
  guarantee real APRS traffic is within range of whatever antenna is
  attached in this environment. No crash, no exception in the backend
  log, `aprs/start`/`aprs/stop` both returned 200, and the capture
  process behaved identically to the spectrum/audio verifications
  from prior entries. The synthetic round-trip test remains the actual
  proof of correctness; this run only confirms the live wiring doesn't
  break.

## Outstanding Work

- Never verified against real over-the-air APRS traffic -- only
  synthetically. If someone runs this near an actual APRS digipeater
  or nearby station, that would be the next real test.
- No clock-recovery PLL, as noted above -- fine for single-packet
  decode at nominal rates, would need real timing recovery for
  anything longer or more clock-drift-sensitive.
- Only FM-modulated AFSK1200 is supported (standard VHF APRS); HF APRS
  (300 baud) and any other AX.25-based mode would need their own baud
  rate / tone-frequency constants at minimum.
- `MessagingCenterWidget`'s non-APRS tabs (Winlink, JS8Call, etc.)
  remain sample data, same as before.
- Same browser-verification gap as recent entries.

## Next Steps

1. Verify against real APRS traffic if this environment ever has
   working antenna access to an active area.
2. Consider a proper PLL-based clock recovery if longer/noisier
   frames turn out to need it in practice.
3. Start Phase 3 (Radio Manager / Hamlib) or a second decoder (e.g.
   NOAA weather radio SAME, or a much larger undertaking, FT8).
4. Get real browser/audio verification once available in this
   environment.

---

# 2026-07-06 — Second Decoder: NOAA Weather Radio SAME

## Summary

Added a second real digital-mode decoder -- NOAA Weather Radio SAME
(Specific Area Message Encoding, the format behind weather/emergency
alert bursts) -- reusing the same phase-offset-brute-force FSK
demodulation approach the APRS decoder established, wired to the
previously-sample-only Alerts widget. Along the way, hit and fixed a
real DSP bug that the APRS decoder's tone spacing had gotten lucky
enough to not expose: SAME's mark/space tones are separated by
*exactly* the baud rate, which is close to a worst-case for the
unwindowed matched-filter approach `afsk.py` uses -- fixed by adding a
Hann window to the correlation kernels, taking the synthetic
round-trip test from ~74% bit accuracy (useless) to 695/696.

## Motivation

The previous entry named this as a next step. Chose SAME over Radio
Manager/Hamlib for the same reason APRS was chosen over FT8 last time:
it's the tractable option given what's actually available to build and
verify against in this environment -- no serial/CAT-capable
transceiver is attached here (checked: no `/dev/ttyUSB*`/`/dev/ttyACM*`,
no `rigctl`), so a Radio Manager subsystem couldn't be verified against
real hardware the way every feature so far has been. SAME reuses the
already-verified RTL-SDR receive path instead.

## Features Added

Backend (`backend/`):

- `app/services/decoders/same.py` (`SameDecoder`): direct (non-NRZI)
  FSK demod -- mark=2083.3Hz is literally bit "1", space=1562.5Hz is
  bit "0", no transition-comparison needed, simpler than AX.25 in that
  respect. Frame sync requires a run of >=8 preamble bytes (0xAB) at a
  given phase offset before trusting it (the analogue of AX.25's
  bit-stuffing self-rejection), then extracts the ASCII "ZCZC-...-"
  header via `parse_same_header` (originator, event code, location
  codes, purge time, timestamp, station ID).
- `StreamService`/`_ReceiverCapture`: `enable_same`/`disable_same`,
  identical lazy-lifecycle shape to `enable_aprs`/`disable_aprs` --
  same capture, same `is_idle()` accounting, decoded alerts emitted as
  `SameAlert` events on the shared EventBus.
- `POST /api/receivers/{id}/same/start` / `/same/stop`.

Frontend (`frontend/`):

- `ReceiverCard` gained a "Decode SAME" toggle alongside "Decode APRS".
- `AlertsWidget` now shows real `SameAlert` events (with a small
  event-code -> severity mapping, e.g. TOR/EWW/FFW/EAN as critical,
  RWT/RMT test codes as info, everything else as warning) when any
  exist, falling back to sample data otherwise -- same pattern as
  `MessagingCenterWidget`'s APRS tab.

## The bug: tone spacing exactly equal to baud rate

SAME's mark/space tones are 2083.3Hz and 1562.5Hz -- separated by
520.8Hz, which is (by design, per the SAME spec) exactly the 520.83
baud symbol rate. A matched-filter correlator's frequency resolution is
roughly 1/(window duration); with a one-symbol-period rectangular
window, that resolution is *also* about 520Hz -- meaning the two tones
sit almost exactly one filter-bin apart, the worst practical case for
a rectangular window's sidelobe leakage. The synthetic round-trip test
caught it immediately: the initial unwindowed implementation decoded
roughly 74% of bits correctly (i.e., useless -- worse than the
self-rejection logic could route around). Applying a Hann window to
the same four correlation kernels (mark/space x cos/sin) suppresses
those sidelobes at the cost of a slightly wider main lobe, and took
the same test to 695/696 bits correct.

AFSK1200 (APRS)'s tones are 1000Hz apart against a coarser ~1200Hz
window resolution -- enough margin that the unwindowed version worked
fine there. This was worth writing down: the *same* demodulation
technique needs different treatment depending on how tight the tone
spacing is relative to the symbol rate, and it's not obvious from the
code alone why one decoder needs a window and the other doesn't
without this context.

## Architecture Decisions

- **Direct FSK (no NRZI) made `SameDecoder` simpler than
  `Afsk1200Decoder`, not shared with it.** The two protocols encode
  bits fundamentally differently (SAME: tone *is* the bit; AX.25: tone
  *change* is the bit), so despite both being "FSK demod + phase-offset
  brute force," a shared base class would have had to parameterize
  around that difference for little benefit -- two small, independently
  readable modules seemed better than one with a branch in the middle.
- **`SameDecoder`'s self-rejection is "require N preamble bytes",
  not bit-stuffing.** SAME has no bit-stuffing (it's not HDLC), so the
  AX.25 decoder's rejection mechanism doesn't apply; requiring a
  genuine run of `0xAB` bytes plays the same role -- garbage from a
  wrong phase offset essentially never produces 8+ consecutive correct
  preamble bytes by chance.
- **Same "enable/disable is a capture-level toggle, not a
  per-connection subscription" choice as APRS**, for the same reason:
  decoded alerts aren't per-client data, they go out on the shared
  event bus.

## Files Created / Modified

- `backend/app/services/decoders/same.py` (new)
- `backend/app/services/stream_service.py` -- `enable_same`/
  `disable_same`, `_decode_same`.
- `backend/app/api/routes/receivers.py` -- `same/start`, `same/stop`.
- `backend/tests/test_same_decoder.py` (new) -- synthetic round-trip
  test with a fractional-sample-accurate test-only SAME/AFSK encoder
  (an integer-samples-per-bit encoder was tried first and produced a
  full bit period of drift over a ~700-bit message -- fixed by tracking
  a running cursor instead of truncating per bit, same principle as
  the decoder's own timing).
- `backend/tests/test_stream_service.py` -- SAME enable/disable and
  shared-capture-with-APRS lifecycle tests.
- `frontend/src/api/receivers.ts` -- `startSameDecoding`/`stopSameDecoding`.
- `frontend/src/components/receivers/ReceiverCard.tsx` -- SAME toggle.
- `frontend/src/components/dashboard/AlertsWidget.tsx` -- real SAME
  alert data.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 34/34 passing, including
  `test_same_round_trip_recovers_known_header` (encodes a known SAME
  header as an actual FSK waveform, decodes it, asserts exact
  recovery) and SAME enable/disable/shared-capture lifecycle tests
  (including sharing one capture with APRS decoding simultaneously).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, tuned the real
  RTL2838 dongle to 162.400 MHz (a standard NOAA Weather Radio
  channel), enabled SAME decoding via the real REST endpoint, listened
  on `/ws/events` for 20 seconds. Zero alerts decoded -- expected and
  reported honestly, same as the APRS entry's live test: there's no
  guarantee of an active NOAA transmitter (or any RF signal at all) in
  range of whatever antenna is attached here, and SAME headers are
  only broadcast periodically/on actual alerts, not continuously. No
  crash, clean `rtl_sdr` process start/stop. The synthetic round-trip
  test is the real correctness proof, as with APRS.

## Outstanding Work

- Never verified against a real over-the-air SAME broadcast -- only
  synthetically, same caveat as APRS.
- No PLL-based clock recovery, same limitation as the APRS decoder
  (fixed nominal bit period, fine for one message's duration at this
  baud rate).
- `parse_same_header` doesn't map location (FIPS) codes or event codes
  to human-readable names -- `AlertsWidget` shows raw codes plus a
  small severity guess, not "Los Angeles County, Tornado Warning."
- Same browser-verification gap as recent entries.

## Next Steps

1. Verify against real SAME/APRS traffic if this environment ever has
   working antenna access to an active area.
2. Add FIPS location code and event code -> human-readable name
   lookup tables for `AlertsWidget`.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available to verify against, or a third decoder.
4. Get real browser/audio verification once available in this
   environment -- now overdue across several entries.

---

# 2026-07-06 — Human-Readable SAME Event/Location Codes

## Summary

Closed the "Add FIPS location code and event code -> human-readable
name lookup tables" item from the previous entry. `AlertsWidget` now
shows real alerts as "Tornado Warning" / "County 037, California"
instead of raw `TOR` / `006037` codes, resolved backend-side so the
lookup tables live in one place rather than being duplicated in the
frontend.

## Motivation

Named directly in the previous entry's outstanding-work list: showing
raw SAME codes in a dashboard widget meant to be human-facing wasn't
really finished. Event codes and state FIPS codes are small, stable,
official tables, so filling them in was a well-scoped, low-risk
addition -- unlike the ~3,200-entry county FIPS database, which was
deliberately left as a numeric code (see below) rather than guessed at
partially.

## Features Added

- `backend/app/services/decoders/same_codes.py` (new):
  `EVENT_CODES` (the ~50 official NWS/EAS SAME event codes -> full
  names), `STATE_FIPS` (all 50 states + DC + territories), and
  `SUBDIVISION_NAMES` (a location code's leading digit -- county
  quadrant, e.g. "Northwest"). `describe_event()` and
  `describe_location()` wrap these with a raw-code fallback for
  anything not in the table.
- `StreamService._decode_same` now adds `event_name` and
  `location_names` (a list, one per SAME location code in the alert)
  to the `SameAlert` event payload alongside the existing raw fields.
- `AlertsWidget` displays `event_name`/`location_names` instead of the
  raw `event_code`/`locations` it showed in the previous entry.

## Architecture Decisions

- **County FIPS codes are shown numerically (`"County 037,
  California"`), not guessed at.** A full US county database is
  ~3,200 entries -- a real dataset to maintain, not a small lookup
  table like event codes or the 51 state entries. Partially embedding
  "the counties I happen to know" would silently produce correct-looking
  output for some alerts and raw fallback for others with no way for a
  user to tell which is which; resolving the state name (always
  correct, small table) while leaving the county numeric (always
  correct, if less friendly) was preferred over a partial table that's
  sometimes wrong-looking-right.
- **Enrichment happens once, backend-side, not duplicated in the
  frontend.** `AlertsWidget` already had to invent its own severity
  classification (event code -> info/warning/critical) client-side
  since that's a presentation decision, not a data-fidelity one -- but
  the actual code -> name mappings are facts about the SAME spec, and
  belong in exactly one place so they can't drift between backend and
  frontend copies.

## Files Created / Modified

- `backend/app/services/decoders/same_codes.py` (new)
- `backend/app/services/stream_service.py` -- `_decode_same` enrichment.
- `backend/tests/test_same_codes.py` (new)
- `backend/tests/test_stream_service.py` -- `_decode_same` end-to-end
  enrichment test (stubs the decoder and event bus directly, since the
  FSK demod itself is already covered by `test_same_decoder.py`).
- `frontend/src/components/dashboard/AlertsWidget.tsx` -- displays the
  enriched fields.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 41/41 passing, including
  6 new `test_same_codes.py` cases (known/unknown event codes, plain
  and subdivision-qualified locations, unknown state FIPS, malformed
  input) and a new `_decode_same` test asserting a stubbed
  `"ZCZC-WXR-TOR-006037+0030-1231423-KLOX/NWS-"` header produces an
  emitted event with `event_name: "Tornado Warning"` and
  `location_names: ["County 037, California"]`.
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- Backend restarted live and confirmed healthy; the enrichment logic
  itself is verified by the stubbed unit test above rather than a live
  over-the-air run, since (per the last two entries) no real
  APRS/SAME traffic has been received in this environment to exercise
  it end-to-end.

## Outstanding Work

- County-level FIPS names are still not resolved (by design, see
  above) -- would need a real ~3,200-entry dataset, not a small
  lookup table.
- Same real-traffic-unverified and browser-verification gaps as the
  last several entries.

## Next Steps

1. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available to verify against.
2. Get real browser/audio verification once available in this
   environment -- now overdue across several entries.
3. If a full county FIPS dataset is ever worth the maintenance cost,
   revisit `describe_location`.

---

# 2026-07-06 — Receiver Tiles Get Real Live Spectrum

## Summary

With Radio Manager blocked on missing serial/CAT hardware and browser
verification blocked on no display, un-mocked another dashboard
widget instead: `ReceiverTileGridWidget`'s per-tile waterfall now
shows real live spectrum data (the same `/ws/spectrum` pipeline
`SpectrumMonitorWidget` already uses) instead of the decorative
`MiniWaterfall` animation, for any receiver with IQ streaming.
`MiniWaterfall.tsx` is now unused by anything and was deleted rather
than left as dead code.

## Motivation

`ReceiverTileGridWidget` was one of the last dashboard widgets still
showing purely decorative data for something the backend has
genuinely supported since the IQ-streaming entry two sessions ago.
With the two "next steps" both blocked on resources this environment
doesn't have (a CAT-capable rig; a display), continuing to close
un-mocking gaps was the highest-value thing available to do with what
*is* here.

## Features Added

- `ReceiverTileGridWidget` extracted a `ReceiverTile` subcomponent
  (hooks can't be called inside `.map()`, so each tile needed to
  become its own component to call `useSpectrumStream` per receiver).
  Each tile subscribes to its own receiver's spectrum stream and
  renders it via the same `SpectrumCanvas`/`liveFrame` mechanism
  `SpectrumMonitorWidget` uses; the "sample" badge now only shows for
  receivers that don't support `iq_streaming` or haven't connected yet.
- `MiniWaterfall.tsx` deleted (no remaining callers).

## Architecture Decisions

- **Mounting this widget now opens a spectrum capture for every
  listed receiver, not just the one a user explicitly picks.** This is
  a real, deliberate change in resource behavior: previously, opening
  the dashboard claimed no hardware at all; now, having Receiver Tiles
  visible claims every IQ-capable receiver's capture for as long as
  the tile is mounted (each subscription is torn down on unmount, same
  as every other `useSpectrumStream` consumer). This was accepted
  because "Receiver Tiles" is explicitly an at-a-glance multi-receiver
  overview -- a mounted overview of all receivers *is* someone
  watching all of them, consistent with the "an unwatched dashboard
  doesn't tie up hardware" principle rather than in tension with it.
- **Extracting a subcomponent rather than restructuring the hook.**
  `useSpectrumStream` already handles connect/reconnect/cleanup
  per-receiver-id; the only change needed was giving each tile its own
  component instance so React's rules of hooks are satisfied, not any
  change to the hook itself.

## Files Created / Modified

- `frontend/src/components/dashboard/ReceiverTileGridWidget.tsx` --
  `ReceiverTile` subcomponent, real spectrum data.
- `frontend/src/components/common/MiniWaterfall.tsx` (deleted).

## Verification

- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean (139 modules, down from 140 with
  `MiniWaterfall` gone).
- Backend unaffected (no backend files touched); `ruff check .` and
  `pytest` (41/41) re-confirmed clean anyway.
- Not independently re-verified against real hardware this entry: the
  underlying `/ws/spectrum` pipeline and `SpectrumCanvas`'s `liveFrame`
  rendering were already verified against the real RTL-SDR in the
  IQ-streaming and receiver-picker entries two sessions ago, and this
  change is a straightforward reuse of both, not new backend surface.
  Actual on-screen rendering remains unverified by eye, same
  browser-access gap as recent entries.

## Outstanding Work

- `SpectrumOverviewWidget` remains deliberately sample-only (a
  full-band view a single narrowband receiver can't honestly provide
  -- see the receiver-picker entry).
- Alerts/Digital Mode Radio/Messaging Center's non-APRS tabs/Digital
  Decodes/Recordings remain sample data pending their own backend
  subsystems.
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps as recent entries.

## Next Steps

1. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available.
2. Get real browser/audio verification once available in this
   environment.
3. Continue un-mocking remaining sample-data widgets as time allows,
   or start a third decoder.

---

# 2026-07-06 — Recording Engine (Phase 8, Audio)

## Summary

Built the first real slice of Phase 8: a `RecordingService` that
records a receiver's demodulated audio to a WAV file on disk, wired to
"Record Audio" on `ReceiverCard` and real data in the previously
sample-only `RecordingsWidget`. Also updated `ROADMAP.md` with a new
"Known Environment Blocks" section per instruction, documenting
*why* Phase 3 (Radio Manager) and browser verification are stalled --
missing real serial/CAT hardware and missing display/headless browser,
respectively -- rather than leaving them as silent gaps.

## Motivation

Both items actionable from the last several entries were genuinely
blocked on resources this environment doesn't have. Rather than force
either one, moved to the next real, verifiable-with-what's-actually-
attached-here piece of work: audio recording reuses the exact
`StreamService.subscribe_audio` queue `/ws/audio` already established,
so it needed no new hardware-claim path -- just a consumer that writes
to a file instead of a socket.

## Features Added

Backend (`backend/`):

- `app/services/recording_service.py` (`RecordingService`): `start()`
  subscribes to `StreamService`'s audio queue (same call `/ws/audio`
  makes) and spawns an `asyncio.Task` that drains PCM16 chunks
  straight into a `wave` file; `stop()` cancels the task, unsubscribes,
  and returns the finished recording's metadata. `list_recordings()`
  scans the recordings directory and reads each WAV's own header
  (`wave.getnframes()`/`getframerate()`) for duration, rather than
  needing a database to track it.
- Recording metadata (receiver, mode, frequency, timestamp) is encoded
  in the filename (`{receiver_id}_{mode}_{freq}_{timestamp}.wav`)
  instead of a database table -- deliberately: recordings are
  immutable files, not editable user data like `ReceiverProfile`.
- New `RecordingSettings.directory` config field
  (`ECHO_BASE_RECORDINGS__DIRECTORY`, default `data/recordings`),
  following the same pattern as `logging.directory`/`plugins.directory`
  -- added specifically so tests could point it at a temp directory
  instead of writing real files into the repo's `data/` on every test
  run.
- `POST /api/receivers/{id}/recording/start` / `/recording/stop`,
  `GET /api/recordings` (list), `GET /api/recordings/{filename}/download`
  (serves the WAV; path-traversal-guarded via resolved-parent-dir check).

Frontend (`frontend/`):

- `ReceiverCard` gained a "Record Audio" toggle (records whatever mode
  is currently selected for Listen).
- `RecordingsWidget` shows real recordings (active ones marked with a
  red dot; completed ones as download links) when any exist, falling
  back to sample data otherwise -- same pattern as every other
  un-mocked widget this session.

`ROADMAP.md`:

- New "Known Environment Blocks" section listing the two genuinely
  stalled items (Radio Manager/Hamlib -- no CAT hardware; browser
  verification -- no display) with what each actually needs to
  unblock, plus a refreshed "Completed"/"In Progress" list -- the old
  one predated this entire multi-session streaming/decoder/recording
  arc and had drifted well behind actual status.

## Bugs Fixed (caught before merge, not shipped)

- **`receiver_id`-in-filename sanitization would have broken the
  "is this receiver currently recording" check.** `receiver_id`
  contains `:` (e.g. `rtl_sdr:00000001`), which gets replaced with `_`
  for the filename. An early version reconstructed `receiver_id` by
  re-parsing the (sanitized) filename for `list_recordings()`'s
  "active" flag, which would never match the real dict key stored in
  `_active` (keyed by the *original*, colon-containing id) -- every
  active recording would have shown as inactive. Fixed by tracking the
  real `receiver_id`/`mode` directly on `_ActiveRecording` and only
  falling back to filename-reconstruction for recordings from past
  runs no longer tracked in memory.
- **`started_at` format was inconsistent between the `start()` response
  (full ISO datetime) and `list`/`stop()` (the filename's compact
  `%Y%m%dT%H%M%SZ` form)**, caught during the live hardware
  verification pass below, not by a test. Fixed by parsing the
  filename timestamp back into the same ISO format everywhere.

## Architecture Decisions

- **A recording is just another `StreamService` audio subscriber, not
  a new capture/hardware-claim path.** Exactly the same reasoning as
  APRS/SAME decoding: the unified-capture entry two sessions ago
  exists specifically so every new audio-consuming feature reuses one
  claim on the hardware instead of adding a competing one.
- **Filename-encoded metadata, no database table.** Recordings are
  immutable, timestamped files; a database row per recording would
  duplicate data already in the file/filename and need its own
  cleanup-on-delete logic. Listing directly from disk means deleting a
  file (e.g. via the filesystem, outside the app) is enough to make it
  disappear from the API -- no orphaned DB rows possible.
- **Recordings directory made configurable rather than hardcoding
  `DATA_DIR / "recordings"`.** Every other per-feature directory
  (logs, plugins) already followed this pattern specifically so tests
  don't write real files into the repository; recordings needed the
  same treatment the moment tests were written, not as an afterthought.

## Files Created / Modified

- `backend/app/services/recording_service.py` (new)
- `backend/app/core/config.py` -- `RecordingSettings`.
- `backend/app/main.py`, `backend/app/api/deps.py` -- `RecordingService`
  wiring, `get_recording_service`.
- `backend/app/api/routes/recordings.py` (new), `backend/app/api/router.py`
- `backend/tests/conftest.py` -- `ECHO_BASE_RECORDINGS__DIRECTORY`
  pointed at the test temp root.
- `backend/tests/test_recording_service.py` (new)
- `config/config.example.yaml` -- documented `recordings.directory`.
- `frontend/src/api/recordings.ts` (new), `frontend/src/types/index.ts`
  -- `RecordingInfo`.
- `frontend/src/components/receivers/ReceiverCard.tsx` -- Record toggle.
- `frontend/src/components/dashboard/RecordingsWidget.tsx` -- real data.
- `ROADMAP.md` -- "Known Environment Blocks" section, refreshed status.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 45/45 passing, including
  4 new `test_recording_service.py` cases (full start/list/stop/download
  lifecycle via the real REST routes, double-start conflicts with 409,
  stopping an unknown recording 404s, auth required).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware, twice** (once before, once after the `started_at`
  fix): restarted the live backend, tuned the actual RTL2838 dongle to
  an FM broadcast frequency, started a recording via the real REST
  endpoint, waited ~4-5 seconds, confirmed it appeared in
  `GET /api/recordings` as active, stopped it, downloaded the WAV, and
  parsed it back with Python's `wave` module: real duration (4-4.36s),
  real file size, and an RMS of ~8500-8550 (of a possible 32768) --
  genuine captured audio, not silence. Also found and killed an
  orphaned `uvicorn` process from an earlier session turn that hadn't
  actually exited when `kill`ed (needed `kill -9`) -- unrelated to this
  feature, just general environment hygiene while verifying live.
- Two real recordings from this verification pass are left in
  `data/recordings/` as evidence the feature works end-to-end, not
  cleaned up as scratch files.

## Outstanding Work

- IQ recording (raw samples, not just demodulated audio) and waterfall
  recording are still unimplemented -- only audio recording exists so
  far, per Phase 8's own remaining-work list.
- No scheduled or triggered (e.g. squelch-activated) recording.
- No recording deletion endpoint -- files can only be removed directly
  on disk.
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps as recent entries (now
  formally tracked in `ROADMAP.md` rather than only in diary entries).

## Next Steps

1. Add a recording deletion endpoint.
2. Consider IQ (raw) recording alongside audio, now that the
   underlying capture already produces both.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available -- both now tracked in `ROADMAP.md`'s "Known Environment
   Blocks."

---

# 2026-07-06 — Recording Deletion

## Summary

Closed the first "Next Steps" item from the previous entry:
`RecordingService.delete()` + `DELETE /api/recordings/{filename}`,
wired to a delete button on completed recordings in `RecordingsWidget`.
Refuses to delete a still-active recording (409, matching the existing
double-start conflict convention) rather than silently stopping it
first.

## Motivation

Directly named as the next step once the recording engine itself
landed -- a recordings library you can add to but never remove from
isn't really finished, and it was small enough to close out before
moving to something larger (IQ recording, or the still-blocked
Phase 3/browser items).

## Features Added

- `RecordingService.delete(filename)`: reuses `path_for()`'s existing
  path-traversal guard, raises `RecordingAlreadyActiveError` (409) if
  the filename belongs to a currently-active recording, otherwise
  unlinks the file.
- `DELETE /api/recordings/{filename}`.
- `RecordingsWidget`: a delete (×) button on each completed recording
  row; active recordings show no delete control (matching the backend
  refusing to delete them) -- stop it first, then delete.

## Architecture Decisions

- **Refuses to delete an active recording rather than auto-stopping
  it.** Silently stopping a recording as a side effect of a delete
  call would be a surprising, easy-to-misread behavior (did they mean
  "stop and delete" or did they click delete on the wrong row?);
  returning a 409 and requiring an explicit stop first matches how
  `start` already refuses to conflict-clobber an existing recording
  rather than restarting it.

## Files Created / Modified

- `backend/app/services/recording_service.py` -- `delete()`.
- `backend/app/api/routes/recordings.py` -- `DELETE /api/recordings/{filename}`.
- `backend/tests/test_recording_service.py` -- delete lifecycle,
  delete-while-active conflict, delete-unknown 404, path-traversal
  rejection tests.
- `frontend/src/api/recordings.ts` -- `deleteRecording`.
- `frontend/src/components/dashboard/RecordingsWidget.tsx` -- delete
  button.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 48/48 passing (45
  previous + 3 new: delete-then-relist confirms removal, deleting an
  active recording 409s, deleting an unknown filename 404s, and a
  path-traversal attempt (`../../conftest.py`) 404s rather than
  deleting something outside the recordings directory).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, then used the real
  `DELETE /api/recordings/{filename}` endpoint against the two actual
  WAV files left over from the previous entry's live recording
  verification (`rtl_sdr_00000001_fm_100300000_...wav`) -- both
  deleted successfully, confirmed gone from both the API listing and
  the filesystem (`data/recordings/` is now empty).

## Outstanding Work

- No bulk delete / retention policy -- one file at a time via the API.
- Same outstanding items as the previous entry: no IQ/waterfall
  recording, no scheduled/triggered recording.
- Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps remain, tracked in
  `ROADMAP.md`.

## Next Steps

1. Consider IQ (raw) recording alongside audio.
2. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — IQ (Raw) Recording

## Summary

Closed the other "Next Steps" item: raw IQ recording alongside the
existing demodulated-audio recording, both selectable from the same
"Record" control on `ReceiverCard`. Required teaching `StreamService`
a third subscriber kind (raw, unprocessed I/Q bytes) alongside
spectrum/audio, since until now every capture consumer wanted
*derived* data, not the raw samples themselves.

## Motivation

Directly named as the remaining option in the previous entry once
recording deletion was done. Raw IQ recording is a real, distinct
capability from audio recording -- it captures everything at a
frequency (all signals in the receiver's instantaneous bandwidth, not
just one demodulated channel), which is what tools like GNU Radio,
inspectrum, or a future decoder replay feature would need as input,
rather than already-demodulated audio.

## Features Added

Backend (`backend/`):

- `StreamService`/`_ReceiverCapture`: `subscribe_iq`/`unsubscribe_iq`
  -- a third subscriber set (alongside spectrum/audio) that receives
  the exact raw interleaved-uint8 bytes read from the plugin's
  `IqStreamHandle`, unprocessed. `is_idle()` now also checks it,
  and a new `sample_rate_hz` property/`get_sample_rate()` exposes the
  capture's actual rate (needed since raw IQ has no self-describing
  header the way a WAV file does).
- `RecordingService`: `mode="iq"` writes a raw binary `.iq` file
  (same format `rtl_sdr`'s own file output uses) via `subscribe_iq`
  instead of a `.wav` via `subscribe_audio`, plus a `.iq.json` sidecar
  holding the sample rate (a raw file has nowhere else to put it).
  `_describe_file` branches on file extension: `.wav` reads its own
  header via the `wave` module; `.iq` reads the sidecar and computes
  duration from `size / 2 / sample_rate_hz`.
- `GET /api/recordings/{filename}/download` now serves `.iq` files as
  `application/octet-stream` instead of forcing `audio/wav` on them.

Frontend (`frontend/`):

- `ReceiverCard`'s Record control gained its own mode selector
  (FM/AM/IQ) independent of the Listen mode selector -- recording IQ
  isn't something you can "listen" to live, so it needed to not be
  coupled to the Listen dropdown's state.

## Architecture Decisions

- **Raw IQ recording is a new `_ReceiverCapture` subscriber kind, not
  a repurposed spectrum/audio one.** Spectrum subscribers get computed
  FFT frames; audio subscribers get demodulated PCM. Recording raw
  samples needed the *unprocessed* bytes already flowing through
  `_run()`'s loop before any of that processing -- broadcasting them
  directly (cheap: an empty subscriber set is checked and skipped, no
  cost when nobody's recording raw IQ) was simpler and cheaper than
  either adding a "raw" pseudo-mode to the audio subscriber dict or
  reconstructing bytes from already-processed data.
- **Filename shape stays uniform (`{receiver_id}_{mode}_{freq}_
  {timestamp}.{ext}`) across both recording kinds**, with the file
  extension (not an extra filename field) distinguishing WAV from raw
  IQ -- keeps `_describe_file`'s parsing logic largely shared, branching
  only on the one thing that's actually different (how to learn the
  sample rate and compute duration).
- **A JSON sidecar for IQ metadata, not a richer container format.**
  Real IQ tools (GNU Radio, inspectrum, SDR#) expect plain raw
  interleaved samples with sample rate conveyed out-of-band (a
  filename convention, a companion file, or manual entry) -- adding a
  custom header to the `.iq` file itself would make it *less*
  directly usable by those tools, not more.

## Files Created / Modified

- `backend/app/services/stream_service.py` -- `subscribe_iq`/
  `unsubscribe_iq`, `sample_rate_hz` property, `get_sample_rate()`.
- `backend/app/services/recording_service.py` -- `mode="iq"` support,
  `.iq`/`.iq.json` handling in `start`/`stop`/`_describe_file`/`delete`.
- `backend/app/api/routes/recordings.py` -- download media type by extension.
- `backend/tests/test_stream_service.py` -- `subscribe_iq` yields raw
  bytes, shares one capture with a spectrum subscriber.
- `backend/tests/test_recording_service.py` -- IQ recording lifecycle
  via the real REST routes.
- `frontend/src/components/receivers/ReceiverCard.tsx` -- separate
  recording-mode selector including "iq".

## Verification

- Backend: `ruff check .` clean; `pytest` -- 51/51 passing (48
  previous + 3 new: `subscribe_iq` yields raw interleaved bytes and
  exposes a sample rate, IQ and spectrum subscribers share one
  capture, and a full IQ-recording REST lifecycle test).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, tuned the actual
  RTL2838 dongle to an FM broadcast frequency, started an IQ recording
  via the real REST endpoint, waited ~4 seconds, stopped it, and
  downloaded the raw file: 1,564,800 bytes at the capture's actual
  240kHz rate (2 bytes/sample) works out to exactly the reported 3.26s
  duration. Byte statistics on the downloaded data: mean 127.5
  (correctly DC-centered uint8 I/Q) with a standard deviation of 13.5
  -- real signal variance, not silence or a constant value. Deleted
  the recording afterward via the real delete endpoint and confirmed
  it was gone from disk.

## Outstanding Work

- No IQ playback/replay feature yet -- recordings exist but there's no
  way to feed a `.iq` file back into the spectrum/audio/decoder
  pipeline within the app (would need external tools like GNU Radio
  today).
- Same outstanding items as recent entries: no scheduled/triggered
  recording, Radio-Manager-blocked-on-hardware, and
  browser-verification-blocked-on-display (tracked in `ROADMAP.md`).

## Next Steps

1. Consider an IQ playback/replay path so a recorded `.iq` file could
   feed back into spectrum/audio/decoders within the app.
2. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — IQ Playback/Replay

## Summary

Closed the last "Next Steps" item from the previous entry: a recorded
`.iq` file can now be "played back" through the exact same
spectrum/audio/decoder pipeline live receivers use, not just
downloaded for use in an external tool. `_ReceiverCapture` never
actually cared whether its samples came from real hardware or a file
on disk -- it just needed something that produces an `IqStreamHandle`
-- so this ended up being a fairly small, targeted refactor rather
than a parallel code path.

## Motivation

The recording feature was "record and download" only; there was no
way to actually watch a recording's spectrum or listen to it within
the app itself, which is most of the point of having recorded it in
the first place. Once IQ recording existed, replaying it through the
same live pipeline was the natural next step, and turned out to be
small because of how `StreamService` was already factored: a capture
is built from whatever produces raw I/Q bytes, and nothing downstream
of that (FFT, demod, decoders) knows or cares about the source.

## Features Added

Backend (`backend/`):

- `_ReceiverCapture` now takes an `open_handle: Callable[[],
  IqStreamHandle]` instead of a `ReceiverPlugin` + calling
  `plugin.open_iq_stream()` itself -- a small refactor that decouples
  it from "must come from a plugin," with no behavior change for live
  receivers (the callable is just `lambda: plugin.open_iq_stream(id)`
  in that case).
- `_RecordingIqStream`: an `IqStreamHandle` that reads from a `.iq`
  file instead of hardware. `read()` returning `b""` at EOF naturally
  ends the capture's run loop exactly like a disconnected live source
  would -- no special "end of playback" handling needed anywhere.
- `StreamService.register_playback(playback_id, path, sample_rate_hz)`
  /`unregister_playback`: makes a file subscribable through
  `playback_id` as if it were a receiver. Every existing subscribe
  method (`subscribe_spectrum`, `subscribe_audio`, `enable_aprs`,
  `enable_same`) works on it completely unchanged -- a playback ID is
  just another key in the same `_captures` dict.
- `RecordingService.sample_rate_for(filename)`: reads a `.iq`
  recording's sidecar for the route layer, which needs it to register
  playback (a raw file's sample rate lives only in that sidecar).
- `POST /api/recordings/{filename}/playback/start` (rejects `.wav`
  recordings with 422 -- there's nothing to re-derive an FFT from
  already-demodulated audio) / `POST .../playback/stop`.

Frontend (`frontend/`):

- `RecordingsWidget` gained a play/stop toggle on completed `.iq`
  recordings, showing a live `SpectrumCanvas` fed by
  `useSpectrumStream(playback_id)` -- the *same* hook and component
  `SpectrumMonitorWidget` uses for live receivers, pointed at a
  playback ID instead of a receiver ID.

## Architecture Decisions

- **A playback ID is a receiver_id from `StreamService`'s point of
  view, not a separate concept with its own subscribe methods.** This
  is what made the feature small: every capability already built on
  top of `_get_or_create` (spectrum, audio, APRS, SAME) came along for
  free the moment `_get_or_create` learned to check a playback
  registry before falling back to `ReceiverService.resolve_plugin`.
  Adding a `subscribe_playback`/parallel API surface would have
  duplicated all of that for no benefit.
- **`StreamService` doesn't depend on `RecordingService`.**
  `RecordingService` already depends on `StreamService` (for
  `subscribe_audio`/`subscribe_iq`); a dependency the other direction
  would be circular. The route layer bridges the two instead --
  `recordings.py` resolves the path and sample rate via
  `RecordingService`, then hands both directly to
  `StreamService.register_playback`.
- **WAV recordings can't be "played back" this way, and the API says
  so explicitly (422) rather than silently doing nothing or
  malfunctioning.** They're already-demodulated PCM audio; there's no
  IQ signal left to FFT or decode. (A WAV recording could get its own,
  separate "play the audio" feature later -- browser-native `<audio>`
  playback of the download URL would work today without any backend
  change, it just isn't wired into the UI yet.)

## Files Created / Modified

- `backend/app/services/stream_service.py` -- `_RecordingIqStream`,
  `_ReceiverCapture` takes `open_handle` instead of `plugin`,
  `register_playback`/`unregister_playback` on `StreamService`.
- `backend/app/services/recording_service.py` -- `sample_rate_for()`.
- `backend/app/api/routes/recordings.py` -- playback start/stop routes.
- `backend/tests/test_stream_service.py` -- updated for the
  `open_handle` constructor param.
- `backend/tests/test_playback.py` (new) -- playback start/stop via
  REST, a playback subscription yielding real FFT frames through the
  actual `_ReceiverCapture` pipeline, WAV-rejected-with-422, unknown
  recording 404s.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 55/55 passing (51
  previous + 4 new `test_playback.py` cases, most notably one that
  records via the mock plugin, starts playback, subscribes to
  `subscribe_spectrum(playback_id)` directly, and asserts a
  correctly-sized real FFT frame comes back through the exact same
  code path a live receiver's spectrum uses).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware, full loop**: restarted the live backend, tuned the
  actual RTL2838 dongle to an FM broadcast frequency, recorded 3
  seconds of real IQ, started playback of that exact file, and opened
  a real WebSocket to `/ws/spectrum/playback:<filename>` -- received
  three real, changing FFT frames (peaks 17.2dB -> 14.3dB -> 13.4dB,
  consistent with playing through a finite recording rather than a
  live/random source). No crash, clean start/stop, recording deleted
  successfully afterward. This is the first feature verified with
  data that round-tripped through real hardware *and* the file system
  *and* back through the live pipeline, not just one or the other.

## Outstanding Work

- No playback speed control, seeking, or looping -- a `.iq` file plays
  through once at its native rate and stops (EOF ends the capture).
- WAV (audio) recordings have no in-app playback yet -- would just be
  a `<audio src={downloadUrl}>` element, no backend work needed.
- Same outstanding items as recent entries: no scheduled/triggered
  recording, Radio-Manager-blocked-on-hardware, and
  browser-verification-blocked-on-display (tracked in `ROADMAP.md`).

## Next Steps

1. Wire browser-native `<audio>` playback for completed WAV recordings
   in `RecordingsWidget` -- no backend change needed, pure frontend.
2. Consider playback controls (seek/loop) if IQ replay turns out to be
   useful enough to want them.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — WAV Playback in RecordingsWidget

## Summary

Closed the small item flagged at the end of the previous entry: a
play/stop toggle on completed WAV (FM/AM audio) recordings in
`RecordingsWidget`, using a plain HTML5 `<audio>` element pointed at
the existing download URL. Pure frontend, no backend change, exactly
as predicted last entry.

## Motivation

Named as a quick follow-up once IQ playback existed: WAV recordings
had a download link but no way to actually listen to one without
leaving the app. Since the backend already serves the file at a
stable URL with the correct `audio/wav` content type, this needed no
new API, just a UI element.

## Features Added

- `RecordingsWidget`: a play/stop (▶/■) button on completed non-IQ
  (FM/AM) recordings, independent of the existing IQ playback toggle.
  Clicking it mounts an `<audio controls autoPlay>` pointed at
  `recordingDownloadUrl(filename)`; `onEnded` resets the toggle back to
  a not-playing state. Switching to a different recording, deleting
  the currently-playing one, or navigating away all correctly tear
  down the audio element (same `key`-based remount / state-cleanup
  pattern already used for the IQ spectrum player above it).

## Architecture Decisions

- **No backend change at all.** The download endpoint already existed
  (from the recording-engine entry) and already sets the right
  `Content-Type`; an `<audio>` element is just another consumer of
  that same URL. Building a dedicated streaming/playback endpoint
  would have duplicated something that already worked.
- **`Content-Disposition: attachment` on the download response was
  left as-is**, even though it's normally associated with forcing a
  "Save As" dialog: HTML5 `<audio>`/`<video>` elements fetch their
  `src` as a media subresource, not a navigation, so browsers play it
  directly regardless of that header -- verified by inspecting the
  actual response headers (`Content-Type: audio/wav`, valid RIFF
  data), not by hearing it play, since no browser is available in this
  environment to confirm audibly.

## Files Created / Modified

- `frontend/src/components/dashboard/RecordingsWidget.tsx` -- audio
  play/stop toggle and `<audio>` element.

## Verification

- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- Backend unaffected (no backend files touched); `ruff check .` and
  `pytest` (55/55) re-confirmed clean anyway.
- **Real hardware, headers only**: recorded ~2 seconds of real FM
  audio from the actual RTL2838, then fetched
  `GET /api/recordings/{filename}/download` directly and inspected the
  response: `Content-Type: audio/wav`, valid `RIFF` magic bytes,
  103,616 bytes. This confirms the resource an `<audio>` element would
  request is valid and correctly typed; it does not confirm the
  browser actually renders playback controls or produces sound, which
  remains unverifiable without a browser in this environment.

## Outstanding Work

- Actual in-browser audio playback (does the `<audio>` element render
  correctly, do controls work, is there audible sound) is unverified --
  same browser-access gap as every frontend feature in recent entries.
- Same outstanding items as recent entries otherwise: no
  scheduled/triggered recording, no IQ playback seek/loop,
  Radio-Manager-blocked-on-hardware, browser-verification-blocked-on-
  display (all tracked in `ROADMAP.md`).

## Next Steps

1. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available.
2. Get real browser/audio verification once available in this
   environment -- overdue across many entries now, the single most
   repeated outstanding item in this diary.
3. Consider scheduled/triggered recording if recording usage grows.

---

# 2026-07-06 — APRS Position Parsing (Phase 9, Partial)

## Summary

Started Phase 9 (Mapping) from its most concrete angle: extracting
latitude/longitude from decoded APRS packets. `parse_aprs_position`
handles the "uncompressed" APRS position report format
(APRS101.pdf ch. 8); `StreamService._decode_aprs` now adds
`latitude`/`longitude`/`symbol` to `AprsPacket` events when a packet's
info field parses as one. `MessagingCenterWidget`'s APRS tab shows
coordinates alongside the message text when present. No map
rendering yet -- this is the data-extraction half of "APRS map," not
the map itself, and the diary/ROADMAP say so explicitly rather than
overclaiming the phase.

## Motivation

Phase 9's ROADMAP list starts with "APRS map," and the APRS decoder
already existed from two sessions ago -- but it only ever surfaced the
raw info-field text, never touched the position data most real APRS
traffic exists to carry. Parsing lat/lon is the part of "map" that's
actually about the protocol (and therefore testable/verifiable without
a browser); rendering pins on a map view is UI work that would join
the growing pile of frontend features blocked on no browser access in
this environment. Doing the verifiable half now, flagging the rest
honestly, seemed better than either skipping it or overclaiming it.

## Features Added

- `app/services/decoders/aprs_position.py` (`parse_aprs_position`,
  `AprsPosition`): parses APRS's uncompressed position format --
  `!`/`=`/`/`/`@` + optional 7-char timestamp + 8-char latitude +
  symbol table ID + 9-char longitude + symbol code + comment --
  returning decimal-degree lat/lon, the symbol, and the comment.
  Explicitly does not attempt the compressed (base-91) or Mic-E
  (position-in-destination-callsign) formats -- both real and common
  in modern APRS traffic, but structurally different enough to be
  their own follow-up.
- `StreamService._decode_aprs`: adds `latitude`/`longitude`/`symbol`
  to the emitted `AprsPacket` event's data whenever
  `parse_aprs_position` succeeds; omitted entirely (not `null`) when a
  packet isn't a position report, so consumers can just check for the
  key's presence.
- `MessagingCenterWidget`: shows `lat, lon` (4 decimal places) next to
  the message text for APRS packets that carry a position.

## Architecture Decisions

- **Only the uncompressed position format is supported, and the
  limitation is stated in the docstring and this entry, not left
  implicit.** Mic-E is actually the more common format on real VHF
  APRS trackers today; supporting only uncompressed means this feature
  will show positions for some real traffic and silently show none for
  the rest. That's an honest, scoped v1 rather than pretending "APRS
  position parsing" is done when only a third of the format space is.
- **Position fields are omitted from the event data rather than sent
  as `null` for non-position packets.** Keeps `AprsPacket` payloads
  smaller for the common non-position case (status messages,
  messages-to-other-stations, telemetry) and lets the frontend check
  `typeof data.latitude === "number"` as a single presence+type test.
- **No map rendering added.** A real map view (station markers,
  zoom/pan, tile imagery) is meaningfully more UI work than a
  coordinates readout, and -- like every other frontend feature this
  session -- couldn't be visually verified in this environment anyway.
  Building it now would mean shipping unverified UI on top of already
  -unverified UI; extracting and displaying the raw coordinates first
  is the smaller, checkable step.

## Files Created / Modified

- `backend/app/services/decoders/aprs_position.py` (new)
- `backend/app/services/stream_service.py` -- `_decode_aprs` enrichment.
- `backend/tests/test_aprs_position.py` (new) -- the canonical
  APRS101.pdf worked example, a timestamped variant, hemisphere sign
  checks, and malformed/non-position/empty-input rejection.
- `backend/tests/test_stream_service.py` -- two new `_decode_aprs`
  tests: a real AX.25 UI frame (built with the same test-only encoder
  helper `test_afsk_decoder.py` uses) carrying a position report
  produces an event with correct lat/lon/symbol; one carrying a
  non-position status message produces an event with no `latitude` key
  at all.
- `frontend/src/components/dashboard/MessagingCenterWidget.tsx` --
  shows coordinates when present.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 63/63 passing (55
  previous + 6 new `test_aprs_position.py` cases + 2 new
  `_decode_aprs` enrichment tests, one of which builds and FCS-verifies
  a *real* AX.25 frame rather than mocking the decoder's output, so the
  full path from raw frame bytes through `parse_ax25_frame` to
  position enrichment is exercised).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, tuned to 144.390 MHz,
  enabled APRS decoding (now running the new position-parsing code
  path on every decoded packet), listened 20 seconds on `/ws/events`.
  Zero packets, as in every previous live APRS attempt in this
  environment -- expected, not a regression. Confirmed no exceptions
  in the backend log and clean `rtl_sdr` process start/stop, i.e. the
  new code path doesn't crash live, even though it couldn't be
  exercised with a real position packet.
- The actual position-math correctness is proven by
  `test_aprs_position.py`'s use of the APRS spec's own worked example
  (`!4903.50N/07201.75W-Test 001234` -> 49.05833, -72.02917), not by
  live reception.

## Outstanding Work

- Compressed and Mic-E position formats are unsupported -- Mic-E in
  particular is common on real hardware APRS trackers, so real-world
  position coverage is partial even once real traffic is received.
- No map view -- coordinates are shown as text, not plotted.
- Never verified against real over-the-air position data, same as
  every APRS/SAME verification since those decoders were built.
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps, tracked in `ROADMAP.md`.

## Next Steps

1. Consider Mic-E position decoding, since it's the more common format
   on real trackers -- non-trivial (position encoded in the
   destination callsign field with its own table-driven encoding), a
   separate piece of work from this entry's uncompressed-format parser.
2. Add an actual map view once real coordinates exist to plot and a
   browser is available to verify rendering.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — APRS Compressed Position Format

## Summary

Added the second APRS position format: "compressed" (base-91 encoded)
position reports, alongside the uncompressed parser from the previous
entry. Deliberately skipped Mic-E again -- same reasoning as last
time, expanded on below -- in favor of a format that's a closed-form
formula rather than a lookup table, and therefore something a
round-trip test can actually prove correct rather than just
self-consistent.

## Motivation

The previous entry's "Next Steps" named Mic-E as the natural
continuation, since it's the more common format on real hardware
trackers. Attempting it anyway surfaced the real reason to hold off:
Mic-E's position data is packed into the *destination callsign field*
via a per-character substitution table (which of ~4 character classes
each of the 6 destination characters falls into determines a digit
*and* a message-type bit *and*, for the last three characters,
N/S/longitude-offset/E-W flags). Transcribing that table from memory
with no real Mic-E packet available in this environment to check
against is exactly the kind of change that could look plausible,
pass a self-written round-trip test (which would only prove the
encoder and decoder agree with *each other*, not with the real
spec), and quietly produce wrong coordinates. The compressed format
doesn't have this problem: it's `symbol_table + base91(lat) +
base91(lon) + symbol + ...`, a specific documented arithmetic formula,
and decoding it is provably the inverse of encoding it -- a round-trip
test genuinely exercises spec compliance, not just internal
consistency.

## Features Added

- `parse_aprs_position` (`aprs_position.py`) now recognizes both
  position formats from the same entry point: after the data type
  character (and timestamp, if present), the next character
  disambiguates them -- a digit means uncompressed (latitude always
  starts with degrees), `/` or `\` means compressed (a symbol table
  ID, never a digit). `_parse_compressed`/`_base91_decode` implement
  the base-91 decode: `latitude = 90 - value/380926`,
  `longitude = -180 + value/190463`, per APRS101.pdf ch. 9.

## Architecture Decisions

- **Still no Mic-E, and the reasoning is written down explicitly in
  the module docstring, not just this diary entry.** The point of
  writing it out in the code itself is so the *next* time someone
  (or a future me) looks at "why doesn't this decode Mic-E packets,"
  the answer -- and the bar for doing it properly (real captured
  packets to check against, not just a from-memory table) -- is right
  there, not buried in diary history.
- **Format disambiguation by first-character type (digit vs. `/`/`\`),
  not a length check or trying both parsers.** This is the standard
  approach real APRS libraries use and is unambiguous for the vast
  majority of real traffic; a table-driven disambiguation would add
  complexity for cases that don't occur in valid data (both formats
  are position-report-specific and don't overlap in their first byte's
  category).

## Files Created / Modified

- `backend/app/services/decoders/aprs_position.py` -- compressed
  format support, explicit no-Mic-E rationale in the docstring.
- `backend/tests/test_aprs_position.py` -- compressed-format round
  trip (encode via the inverse formula, decode, assert recovery),
  southern-hemisphere and timestamped variants.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 66/66 passing (63
  previous + 3 new compressed-format tests, including a genuine
  round-trip: encoding a known lat/lon into base-91 via the inverse of
  the exact formula the decoder uses, then decoding it back and
  asserting recovery to within ~0.001 degrees, i.e. within one
  base-91 encoding step's resolution).
- Frontend: unaffected (no frontend files touched this entry).
- **Real hardware**: restarted the live backend, tuned to 144.390 MHz,
  enabled APRS decoding (now checking both position formats on every
  decoded packet), listened 20 seconds. Zero packets, as in every
  previous live attempt -- expected, not a regression. No exceptions,
  clean `rtl_sdr` process start/stop.

## Outstanding Work

- Mic-E remains unimplemented, deliberately, pending either real
  captured Mic-E traffic to verify against or a very carefully
  cross-checked transcription of the destination-address table.
- No map view still -- coordinates are text, not plotted, for both
  position formats now.
- Same real-traffic-unverified, Radio-Manager-blocked-on-hardware, and
  browser-verification-blocked-on-display gaps as recent entries,
  tracked in `ROADMAP.md`.

## Next Steps

1. If Mic-E is worth doing, get real captured Mic-E packets first
   (e.g. from a public APRS-IS feed or a real local tracker) to
   validate against, rather than transcribing the table blind again.
2. Add an actual map view once a browser is available to verify
   rendering.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — Signal Detection / Peak Analysis (Phase 4)

## Summary

Added Phase 4's "Signal detection" / "Peak analysis" items: a
`PeakTracker`/`find_peak_bins` module that finds distinct local maxima
in the spectrum FFT already computed for every capture, emitting
`SignalDetected` events (frequency + power) via the same EventBus
pattern APRS/SAME use. Two real bugs were found and fixed by testing
against the actual attached RTL-SDR rather than only synthetic data --
both are worth reading in full below, since they're the kind of thing
that looks correct in a unit test and falls over immediately on real
hardware.

## Motivation

"Signal detection" and "Peak analysis" are two of the few remaining
Phase 4 items that don't require new hardware or a browser to build
and verify -- they're pure DSP on top of the spectrum FFT `_run()`
already computes for every capture. A natural next slice given what's
actually buildable/verifiable in this environment right now.

## Features Added

- `app/services/signal_detection.py`: `find_peak_bins` (local maxima
  at least `margin_db` above the spectrum's own estimated noise
  floor), `bin_to_frequency_offset_hz`, `PeakTracker` (bucket + cooldown
  based re-trigger suppression), `estimate_noise_floor_db` (median
  magnitude).
- `StreamService`/`_ReceiverCapture`: `enable_signal_detection`/
  `disable_signal_detection`, same idempotent/EventBus-emitting shape
  as `enable_aprs`/`enable_same`. Computing the FFT is now gated on
  `spectrum_subscribers OR signal_detection_enabled` (previously only
  the former), since detection needs the same magnitude array spectrum
  viewers do, whether or not anyone's watching the waterfall.
- `POST /api/receivers/{id}/signal-detection/start` (`margin_db`,
  default 15.0) / `.../stop`; `ReceiverCard` gained a margin input +
  toggle, matching the APRS/SAME toggle pattern -- detections show up
  in the Activity Feed/System Log automatically, no new widget needed.

## Two real bugs, found live, not in a test

**Bug 1: bin-tolerance re-trigger suppression was nowhere near
enough.** The first implementation suppressed re-detecting "the same"
peak by checking if it was within 2 bins of one seen last frame.
Verified against the real attached RTL-SDR tuned to an FM broadcast
frequency: one real carrier produced 606KB of `SignalDetected` events
in 10 seconds. A real signal's peak bin wanders by far more than a
couple of bins frame-to-frame (modulation, noise) -- this is exactly
the kind of thing a unit test with a static synthetic spectrum would
never catch, because the whole bug is about frame-to-frame *movement*.
Fixed with `PeakTracker`: group bins into coarser buckets and cool
each bucket down for 5 seconds after it triggers -- the same shape
real scanner/signal-detect software uses.

**Bug 2: absolute dB thresholds don't mean anything on this receiver's
raw FFT scale.** Even after fixing the re-trigger bug, testing at
`threshold_db=-20` produced 256 events in 10 seconds -- not a
suppression bug this time, but genuinely ~128 distinct "peaks" across
the whole band, because `20*log10(magnitude)` isn't calibrated to any
physical reference and shifts entirely with gain: at the receiver's
auto-gain setting, nearly the *entire* spectrum sat above -20dB.
Confirmed by manually setting a low fixed gain (10) -- the same
threshold then found *zero* peaks, since the whole scale had shifted
down. The fix: `margin_db` is now relative to the spectrum's own
estimated noise floor (median magnitude, robust to the few bins an
actual signal occupies), not an absolute value. Re-tested at auto gain
with `margin_db=15`: 6 detections in 10 seconds, clustered on a real
adjacent FM station a few hundred kHz off the tuned frequency, with
sane, physically plausible power readings. Both the API field and the
`ReceiverCard` UI were renamed `threshold_db` -> `margin_db` to make
this relative meaning explicit rather than implicit.

## Architecture Decisions

- **Peak-finding, tracking, and noise-floor estimation are pure
  functions/a small stateful class in their own module**, same
  reasoning as `dsp.py`: this is math that's easy to get subtly wrong,
  and keeping it separate from `stream_service.py`'s threading means it
  can be (and was) unit tested directly against controlled synthetic
  spectra -- which is exactly what caught the noise-floor issue's
  *fix* being correct, even though the original *bug* only showed up
  live (synthetic single-peak spectra don't have the "everything is
  bright" problem a real crowded band does).
- **Relative (noise-floor-margin) threshold, not absolute.** This is
  standard practice in real signal-detection/scanner software for
  exactly the reason found here: raw FFT bin magnitude isn't a
  calibrated physical quantity, so a fixed number only "works" for
  whatever gain happened to be active when it was chosen.
- **FFT computation for signal detection reuses the spectrum
  subscriber's exact code path** (same window, same `FFT_SIZE`, same
  per-read cadence) rather than a separate computation -- one
  magnitude array serves both the waterfall and the detector when
  both are active, matching the "one hardware claim, multiple
  consumers" principle established by spectrum/audio/decoders.

## Files Created / Modified

- `backend/app/services/signal_detection.py` (new)
- `backend/app/services/stream_service.py` -- `enable_signal_detection`/
  `disable_signal_detection`, `_detect_signals`, FFT gating change.
- `backend/app/schemas/receiver.py` -- `SignalDetectionRequest.margin_db`.
- `backend/app/api/routes/receivers.py` -- signal-detection start/stop routes.
- `backend/tests/test_signal_detection.py` (new) -- peak finding,
  noise-floor estimation, cooldown/bucket suppression (including a
  test asserting the *same* margin catches a peak regardless of the
  spectrum's absolute dB scale -- the actual live-found bug, made
  reproducible).
- `backend/tests/test_stream_service.py` -- signal-detection lifecycle,
  shared-capture-with-spectrum, and a direct `_detect_signals` test
  with a controlled synthetic spectrum checking bin-to-frequency math.
- `backend/tests/test_receivers.py` -- signal-detection start/stop via REST.
- `frontend/src/api/receivers.ts`, `ReceiverCard.tsx` -- margin input + toggle.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 81/81 passing (75
  previous + 10 new `test_signal_detection.py` cases including the
  noise-floor-adaptive-threshold test, plus lifecycle/REST/enrichment
  tests in the other files).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware, twice, finding two real bugs**: first pass (bin-
  tolerance suppression) produced 606KB/10s of events against a real
  FM carrier -- caught and fixed. Second pass (absolute threshold)
  produced 256 events/10s at auto-gain, 0 events/10s at a manually-set
  low gain with the same threshold -- caught and fixed by making the
  threshold noise-floor-relative. Final re-verification at auto gain
  with the fixed `margin_db=15`: 6 sane detections in 10 seconds,
  correctly landing on a real adjacent FM station's frequency with
  plausible power readings. No crashes, clean process lifecycle
  throughout all three live runs.

## Outstanding Work

- Peak power readings are still on the receiver's raw uncalibrated
  scale (now noise-floor-relative for detection purposes, but the
  reported `power_db` in the event itself is still the absolute raw
  value) -- fine for relative comparison, not a real dBm/dBFS figure.
- No RF heat maps, occupancy analysis, signal history, or receiver
  comparison yet -- Phase 4's other remaining items.
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps, tracked in `ROADMAP.md`.

## Next Steps

1. Consider signal history (logging detections over time) or occupancy
   analysis (what fraction of the band is occupied) as the next Phase
   4 items, now that peak detection exists to build on.
2. Add an actual map view once a browser is available to verify
   rendering.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — Occupancy Analysis (Phase 4)

## Summary

Added Phase 4's "Occupancy analysis": `OccupancyTracker` keeps a
continuously-updated per-bin exponential moving average of "was this
bin above the noise floor by `margin_db`", exposed as a pollable
gauge (`GET .../occupancy`) rather than discrete events, since
occupancy is a running state, not a series of occurrences. Builds
directly on `signal_detection.py`'s noise-floor-relative threshold
work from the previous entry -- same underlying margin concept,
different aggregation.

## Motivation

Named directly as the next Phase 4 item once peak detection existed.
Occupancy ("what fraction of the band has been busy recently") is a
natural complement to peak detection ("what's on right now") and
reuses the exact same per-frame FFT and noise-floor-margin logic, just
accumulated over time instead of triggering one-shot events.

## Features Added

- `OccupancyTracker` (`signal_detection.py`): one float per FFT bin,
  updated each frame via `occupancy = decay*occupancy + (1-decay)*hit`
  where `hit` is 1 if that bin was >= noise_floor + margin_db this
  frame. Constant memory/per-frame cost regardless of how long
  tracking has run, unlike storing a window of raw frames.
- `StreamService`/`_ReceiverCapture`: `enable_occupancy`/
  `disable_occupancy` (same idempotent shape as signal detection),
  plus `occupancy_snapshot()`/`get_occupancy()` -- a point-in-time read
  of current per-bin occupancy, since (unlike APRS/SAME/signal
  detection) there's nothing to push as a discrete event here; a
  client polls a gauge.
- `POST /api/receivers/{id}/occupancy/start` (`margin_db`) / `.../stop`,
  `GET /api/receivers/{id}/occupancy` (422 if not enabled -- there's no
  sensible "occupancy so far" for a receiver nobody asked to track).
- `ReceiverCard` gained a "Track Occupancy" toggle that polls the
  snapshot every 3 seconds and shows a one-line summary (average
  occupancy %, busiest frequency) rather than a full heatmap -- a
  heatmap is real UI work that (like every other visual feature this
  session) can't be verified without a browser; a text summary can be
  confirmed correct by reading the numbers.

## Architecture Decisions

- **A pollable gauge, not events.** APRS packets, SAME alerts, and
  signal detections are all discrete occurrences -- "a thing happened,"
  which is exactly what the EventBus is for. Occupancy is a
  continuously-valid measurement -- "what's the state right now" --
  and forcing that into a stream of events (e.g. re-emitting on every
  change) would mean clients reconstructing a gauge from a change log
  for no benefit over just asking for the current value directly.
- **Exponential moving average, not a stored frame window.** A
  ring buffer of the last N frames' hit/no-hit arrays would give
  identical "recent occupancy" semantics but with memory proportional
  to window length; the EMA gives the same "recent, not all-time"
  behavior in one float per bin, at the cost of not being able to
  answer "occupancy over exactly the last 10.0 seconds" precisely
  (it's an exponentially-weighted approximation of that). For a
  live-monitoring gauge, that trade was worth it.
- **Same `margin_db` concept, reused rather than reinvented.**
  Occupancy needed exactly the same "relative to the noise floor, not
  an absolute scale" fix signal detection already required (same
  uncalibrated FFT scale problem) -- this entry didn't have to
  rediscover that live, because `estimate_noise_floor_db` already
  existed from fixing it last time.

## Files Created / Modified

- `backend/app/services/signal_detection.py` -- `OccupancyTracker`.
- `backend/app/services/stream_service.py` -- `enable_occupancy`/
  `disable_occupancy`/`occupancy_snapshot`/`get_occupancy`, FFT-needed
  gating extended to occupancy.
- `backend/app/api/routes/receivers.py` -- occupancy start/stop/get routes.
- `backend/tests/test_signal_detection.py` -- `OccupancyTracker`
  convergence-toward-100%-when-always-occupied and decay-when-signal-
  disappears tests.
- `backend/tests/test_stream_service.py` -- occupancy lifecycle,
  snapshot shape, shared-capture-with-spectrum tests.
- `backend/tests/test_receivers.py` -- occupancy start/stop/query via
  REST, including the 422-when-not-enabled case.
- `frontend/src/api/receivers.ts`, `ReceiverCard.tsx` -- occupancy
  toggle + polled summary.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 90/90 passing (81
  previous + 9 new: 4 in `test_signal_detection.py`, 4 lifecycle/
  snapshot tests in `test_stream_service.py`, 2 REST tests in
  `test_receivers.py` -- some overlap rounds to 9 net new, all green).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware**: restarted the live backend, tuned the actual
  RTL2838 to the same FM broadcast frequency used in the signal-
  detection entry, enabled occupancy tracking, and polled the real
  snapshot every 2 seconds for 10 seconds. The busiest bins correctly
  landed on the *same* adjacent-station frequencies (~100.386-100.413
  MHz) the previous entry's signal detection independently found,
  with small (0-0.5%) but nonzero occupancy consistent with an
  intermittent/marginal real signal rather than noise -- two
  independently-built features agreeing on the same real-world
  finding is a stronger correctness signal than either alone. No
  crashes, clean process lifecycle.

## Outstanding Work

- No RF heat map (spatial/visual) or signal history (occupancy over
  time, not just current EMA) -- Phase 4's two remaining items.
- No receiver comparison (side-by-side occupancy/signal-detection
  across multiple receivers).
- Occupancy summary in the UI is a one-line average + peak, not a
  visual heatmap -- same browser-verification constraint as recent
  entries.
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps, tracked in `ROADMAP.md`.

## Next Steps

1. Consider signal history (persisting detections/occupancy over time
   rather than just a live EMA) as the next Phase 4 item.
2. Add an actual map/heatmap view once a browser is available to
   verify rendering.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.

---

# 2026-07-06 — Signal History (Phase 4)

## Summary

Closed Phase 4's last remaining item that doesn't need new hardware or
a browser: `SignalDetected` events are now persisted to a real
database table (`signal_detections`) via an `EventBus` subscriber, and
queryable per-receiver/time-range via `GET
/api/receivers/{id}/signal-history`. Distinct from the existing
`/api/events` history, which is in-memory, bounded to 500 events
*of any type*, and gone on restart -- verified live that these records
specifically survive a full backend restart.

## Motivation

The previous entry named this as the next Phase 4 item. It's also the
most natural, since `SignalDetected` events already flow through the
`EventBus`, and persistence just means subscribing another handler to
it (the same pattern `ConnectionManager`'s WebSocket fan-out already
is) -- no new capture logic, no new StreamService concept.

## Features Added

- `SignalDetectionRecord` (`app/db/models/signal_detection.py`) +
  migration `0004_add_signal_detections.py`: receiver_id, frequency_hz,
  frequency_offset_hz, power_db, detected_at (indexed on both
  receiver_id and detected_at for the time-range queries below).
- `app/services/signal_history.py`: `persist_signal_detected` (an
  `EventBus` handler, subscribed in `main.py`'s lifespan alongside
  `ConnectionManager`) and `query_signal_history(receiver_id, minutes,
  limit)`.
- `GET /api/receivers/{id}/signal-history?minutes=60&limit=200`.
- `ReceiverCard` shows a "N detection(s) in the last hour" line,
  polled every 5 seconds while signal detection is enabled.

## Architecture Decisions

- **A plain `EventBus` subscriber, not something `StreamService` calls
  directly.** `StreamService` already has no idea whether anything is
  listening to what it emits -- that's the entire point of routing
  through the event bus rather than a direct method call. Persistence
  is just one more thing that happens to be listening, exactly like
  the WebSocket fan-out already is; `StreamService` didn't need to
  change at all.
- **A dedicated table, not reusing the in-memory `EventBus.recent()`
  history.** That history is intentionally generic (every event type,
  fixed-size ring buffer, gone on restart) -- fine for "what just
  happened," wrong for "how many signals has this receiver seen in the
  last hour," which needs to survive restarts and be filterable by
  receiver and time range, i.e. actual query capability a deque can't
  give you.

## Files Created / Modified

- `backend/app/db/models/signal_detection.py` (new),
  `backend/app/db/models/__init__.py` -- registers the new model.
- `backend/alembic/versions/0004_add_signal_detections.py` (new)
- `backend/app/services/signal_history.py` (new)
- `backend/app/main.py` -- subscribes `persist_signal_detected` to the
  `EventBus`.
- `backend/app/api/routes/receivers.py` -- `GET .../signal-history`.
- `backend/tests/test_signal_history.py` (new) -- persist/query round
  trip, per-receiver filtering, limit handling, auth requirement, and
  an end-to-end test that enables real signal detection on the mock
  plugin's capture and waits for a genuinely-persisted, REST-queryable
  record rather than stubbing the subscriber.
- `frontend/src/api/receivers.ts`, `ReceiverCard.tsx` -- history count
  readout.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 95/95 passing (90
  previous + 5 new, including the end-to-end persistence test above).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings, none
  new); `tsc -b && vite build` clean.
- **Real hardware, restart survival specifically tested**: restarted
  the live backend, tuned the actual RTL2838 to the same FM broadcast
  frequency used in prior entries, ran signal detection for 15
  seconds -- 51 real detections persisted, landing in the same
  adjacent-station frequency range (~100.35-100.39MHz) found by both
  the signal-detection and occupancy-analysis entries. Then
  **restarted the backend again** and re-queried the same endpoint:
  all 51 records were still there. This is the specific property that
  distinguishes this from the existing in-memory event history, so it
  was the specific thing verified, not just "does it save at all."
  Test data (those 51 detection rows) remains in `data/echo-base.db`
  as evidence, same as the recording-engine entries left real WAV/IQ
  files.

## Outstanding Work

- No UI for browsing signal history beyond a live count -- no
  frequency/time chart, no export.
- No automatic pruning/retention policy -- the table grows unbounded
  as long as signal detection runs.
- No RF heat maps or receiver comparison yet -- Phase 4's two
  remaining items, both meaningfully UI-heavy (a heat map is exactly
  the kind of thing that needs a browser to verify).
- Same Radio-Manager-blocked-on-hardware and
  browser-verification-blocked-on-display gaps, tracked in `ROADMAP.md`.

## Next Steps

1. Add retention/pruning for `signal_detections` before it grows
   unbounded in a long-running deployment.
2. Add an actual map/heatmap view (Phase 4's remaining items) once a
   browser is available to verify rendering.
3. Start Phase 3 (Radio Manager / Hamlib) once real serial/CAT
   hardware is available, or get real browser/audio verification once
   available.
## Fixed: Listen/Record silently going dead after a capture crash

The user reported that live audio ("Listen"), which had worked
earlier in the session, now produced no sound at all, and asked for
recording/playback to be confirmed too.

Backend logs showed a defunct `[rtl_sdr] <defunct>` zombie process
from earlier in the session, and manually invoking `rtl_sdr` against
the real dongle worked fine standalone -- so the hardware and the
`rtl_sdr` binary were never the problem. The real bug was in
`StreamService`: `_ReceiverCapture._run()` (the background thread that
reads IQ off the `rtl_sdr` subprocess and fans it out to
spectrum/audio/recording subscribers) can exit on its own if the
subprocess dies (crash, `PLL not locked!` glitch, anything), but
nothing ever removed the now-dead `_ReceiverCapture` from
`StreamService._captures`. Every subsequent `subscribe_audio` /
`subscribe_iq` call (Listen, Record, APRS, SAME, spectrum) found the
stale entry via `_get_or_create` and happily attached a new subscriber
queue to a thread that would never broadcast to it again -- no
exception, no error, just silence forever until the backend was
restarted. This explains the "it worked, then stopped, for
everything" shape of the report: one crashed capture (from whatever
first triggered it) poisoned every feature sharing that receiver_id
from that point on.

Fix: added `_ReceiverCapture.is_alive()` (checks the worker thread),
and `StreamService._get_or_create` now detects a dead-but-still-cached
capture, drops it, and spins up a fresh one instead of reusing it.
Also fixed a related zombie-process leak in the `rtl_sdr` plugin's
`_RtlSdrIqStream.close()`: it called `kill()` after a `terminate()`
timeout but never `wait()`-ed afterward, leaving an actual `<defunct>`
zombie in the process table (visible via `ps aux`) -- this was the
smoking gun that pointed at a completed-but-uncleaned capture in the
first place.

**Verified against real hardware after restarting the backend with
the fix:**
- **Listen**: `/ws/audio/rtl_sdr:00000001?mode=fm` -- real PCM16,
  RMS ~7800-9300, full dynamic range.
- **Recording**: a 6-second FM recording produced a real 469KB/4.89s
  WAV (RMS ~8484, full range) -- before the fix, the identical
  recording call against the poisoned capture produced a 44-byte
  (header-only, zero-frame) file.
- **Playback**: recorded 3s of IQ, started playback, subscribed to
  `/ws/spectrum/{playback_id}` -- real FFT frames (peaks 17.5-24dB)
  came back, then cleaned up (deleted) the test recording.

All test recordings created during this verification were deleted
afterward via the real `DELETE /api/recordings/{filename}` endpoint,
consistent with every other real-hardware verification entry in this
diary.

## Added: Capture health monitoring (Phase 2)

A direct follow-on to the previous entry's bug (a crashed capture
worker silently poisoning every feature sharing its receiver_id,
forever, with zero visible error). The `is_alive()` fix stops it from
persisting, but a capture can still legitimately stall for other
reasons (device unplugged mid-stream, a future regression of the same
class) -- there was no way to *see* that from the API or UI, only to
notice "nothing's happening" after the fact.

- `_ReceiverCapture` now tracks `last_read_at` (monotonic) and a
  running `read_count`, updated every successful `handle.read()` in
  the capture loop.
- `_ReceiverCapture.health()` / `StreamService.capture_health()`:
  worker-thread liveness, last-read age in seconds, and
  spectrum/audio/IQ subscriber counts.
- `GET /api/receivers/{id}/capture-health` (any authenticated role,
  same as `GET /api/receivers/{id}`): `{"active": false}` if nobody's
  subscribed to anything, otherwise the full health snapshot above.
- Frontend (`ReceiverCard.tsx`): polls this every 4s whenever
  Listen/Record/APRS/SAME/signal-detection/occupancy is toggled on,
  and shows a "Capture stalled -- no samples received recently" badge
  if the thread has died or gone >3s without a read.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 95/95 passing (no test
  changes needed; this is additive instrumentation, not new decode
  logic).
- Frontend: `npm run lint` clean (same 2 pre-existing warnings);
  `tsc -b && vite build` clean.
- **Real hardware**: tuned the actual RTL2838 to 100.3MHz and started
  a recording. `capture-health` correctly reported `active: false`
  before subscribing, `active: true, alive: true, read_count: 27,
  last_read_age_seconds: 0.38` ~1.5s into the recording, and back to
  `active: false` immediately after stopping. Test recording deleted
  afterward via the real API, same as every other hardware-verified
  entry.

## Next Steps

1. Receiver profile calibration (Phase 2's remaining item).
2. Revisit Phase 3 (Radio Manager) once real CAT/serial hardware is
   available; revisit browser-based UI verification once a display or
   headless browser is available (`ROADMAP.md`'s Known Environment
   Blocks).

## Added: Suggested receiver profile presets

Scoped down from the ROADMAP's "Receiver Profiles: ADS-B, Airband,
APRS, NOAA, AIS, Amateur..." list -- most of those are full protocol
decoders (ADS-B/AIS in particular need a very different high-rate
capture path than the current FM/AM-oriented one, out of scope for one
slice), but the *profile* half of that list -- "what frequency/gain do
I tune to for band X" -- is a small, real, immediately useful feature
on its own, and every entry chosen is within an RTL2832U/R820T's
tunable range so it's a genuinely usable preset, not a placeholder.

- `backend/app/services/suggested_profiles.py`: a static (non-DB) list
  of 7 presets -- FM Broadcast, NOAA Weather Radio (SAME-decoder-
  tagged), APRS 2m (AFSK1200-decoder-tagged), Marine VHF ch16, 2m
  amateur calling, airband guard, and ADS-B 1090MHz (frequency only --
  flagged in its own description as "no decoder built yet").
- `GET /api/receiver-profiles/suggested`: any authenticated role.
- Frontend: `ReceiverProfilesPanel` now has a "Suggested Presets"
  section above the create form, each with an "Add" button that calls
  the existing `createReceiverProfile` (becoming a normal, editable,
  deletable profile from then on -- no new data model, no special-
  cased "suggested" profile type to maintain). Already-added presets
  (matched by frequency) show "Saved" instead and are disabled.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 95/95 passing (no new
  tests needed -- this endpoint returns a static list, no branching
  logic to unit-test beyond what FastAPI/pydantic already validate).
- Frontend: `npm run lint` clean (2 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware, full round-trip**: fetched the 7 suggested
  presets, created a real profile from the "APRS (2m Packet)" preset,
  applied it to the actual RTL2838 -- confirmed the receiver actually
  retuned to 144.39MHz with gain "auto" -- then deleted the test
  profile via the real DELETE endpoint.

## Next Steps

1. ADS-B decoding needs its own higher-sample-rate capture path
   (StreamService's current design is FM/AM-audio-rate-oriented) --
   worth a dedicated design pass before starting, not a drop-in like
   APRS/SAME were.
2. Same Radio-Manager/browser-verification environment blocks as ever
   (`ROADMAP.md`).

## Added: profile-apply auto-enables its decoder, capture-health syncs UI state

A follow-on to the suggested-profiles entry above: the "decoder" field
on a profile (already there for "APRS"/"SAME") was carried through to
the API but never actually used by `apply_profile` -- applying the
"NOAA Weather Radio" preset retuned the receiver but didn't start SAME
decoding, so "one click" wasn't really one click yet.

- `apply_profile` now calls `stream_service.enable_aprs`/`enable_same`
  when `profile.decoder` is `"aprs"`/`"same"`. Only ever turns a
  decoder *on* -- switching profiles never stops one a user already
  started, matching how every other decoder toggle in this app works
  (explicit stop only).
- This exposed a real gap: `ReceiverCard`'s aprsEnabled/sameEnabled/
  signalDetectionEnabled/occupancyEnabled are local component state,
  never synced from the backend. Enabling a decoder via profile-apply
  (or, previously, page reload while a decoder was running) would
  leave the UI showing "Decode APRS" (off) while it was actually on.
  Fixed by having `_ReceiverCapture.health()` report all four enabled
  flags, and switching `ReceiverCard`'s capture-health poll (added in
  the capture-health entry above) to always run (not just while
  something's toggled on locally) and sync those four booleans from
  the server every 4s.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 95/95 passing.
- Frontend: `npm run lint` clean (2 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware**: created a real profile from the APRS suggested
  preset, confirmed `capture-health` reported `aprs_enabled: false`
  before applying it, applied it to the actual RTL2838, and confirmed
  `capture-health` reported `aprs_enabled: true` immediately after --
  with no separate "start APRS" call made. Cleaned up (stopped
  decoding, deleted the test profile) via the real API afterward.

## Next Steps

1. Extend the same "decoder" auto-enable pattern to signal detection/
   occupancy once profiles have a natural way to carry a margin_db
   (they don't yet -- out of scope for this slice).
2. Same environment blocks as ever (`ROADMAP.md`).

## Added: Toast notification system (Phase 1)

Picked up the last remaining Phase 1 frontend item: a notification
system distinct from the raw event feed (Activity Feed/System Log
widgets already show every event, forever -- toasts are for the
handful worth interrupting the user for, and they go away on their
own).

- `context/ToastContext.tsx`: `ToastProvider`/`useToast()` -- a small
  stack (max 5, oldest dropped), each auto-dismissing after 8s or on
  manual dismiss.
- `components/common/ToastContainer.tsx`: fixed bottom-right stack,
  info/warning/danger variants.
- `components/common/EventToastBridge.tsx`: watches the shared
  `EventStreamContext` events (already deduped/capped at 50 by
  `useEventStream`) and toasts exactly three event types --
  `SameAlert` (a real NOAA/EAS emergency alert, rare and worth
  surfacing), and `ReceiverStarted`/`ReceiverStopped` (confirmation of
  an action the user just took). Deliberately *not* `AprsPacket` or
  `SignalDetected` -- both fire often enough in normal operation that
  toasting each one would just be noise on top of what the Activity
  Feed already shows.
- Both mounted once in `AppShell`, inside `EventStreamProvider` so
  they share its one WebSocket connection rather than opening another.

One real shape bug caught before it shipped: `ReceiverStarted`/
`ReceiverStopped` events are emitted with `source="plugin:rtl_sdr"` --
the actual receiver_id lives in `data.receiver_id`, confirmed by
connecting to `/ws/events` directly and triggering a real start/stop.
An early draft used `event.source` directly, which would have toasted
"plugin:rtl_sdr started" instead of "rtl_sdr:00000001 started".

## Verification

- Frontend: `npm run lint` clean (3 warnings -- the 2 pre-existing
  ones plus the same react-refresh-only-exports-components shape on
  `ToastContext.tsx` that `AuthContext`/`EventStreamContext` already
  have, not a new class of issue); `tsc -b && vite build` clean.
- Backend: unchanged; `pytest` -- 95/95 passing (sanity check only).
- **Real hardware/event shapes**: connected directly to `/ws/events`
  and triggered a real receiver start/stop via the REST API, confirmed
  the exact event shape (`source`/`data.receiver_id`) `EventToastBridge`
  depends on. `SameAlert`'s `event_name`/`location_names` fields
  cross-checked directly against `stream_service.py`'s `_decode_same`
  (no live NOAA alert was received to trigger one for real -- same
  environment block as every other real-decode-verification entry).
- Could not visually verify toast rendering/stacking/dismissal itself
  -- no browser available in this environment (`ROADMAP.md`'s Known
  Environment Blocks).

## Next Steps

1. Accessibility and responsive-layout pass (Phase 1's last remaining
   frontend item) -- needs a browser to verify properly.
2. Same environment blocks as ever.

## Added: APRS station persistence (Phase 9 groundwork)

The ROADMAP's Phase 9 "APRS map" item needs two things: a real map/tile
UI (needs a browser to build against properly) and a data layer
tracking "where's each station currently reporting from" (doesn't).
Built the second half this slice, same "persist events via an
EventBus subscriber" shape as `signal_history.py`.

- `aprs_stations` table (migration 0005): one row per
  `(receiver_id, callsign)`, upserted on every position-bearing
  `AprsPacket` event -- last known position, not a full track/
  breadcrumb history (that's a bigger addition, noted as a possible
  follow-up). Packets without a decoded position (most real APRS
  traffic isn't a position report, and Mic-E specifically isn't
  decoded yet -- see the existing `aprs_position.py` docstring) are
  correctly skipped rather than persisted with garbage coordinates.
- `services/aprs_stations.py`: `persist_aprs_station` (the subscriber,
  wired in `main.py` alongside `persist_signal_detected`) and
  `query_aprs_stations(receiver_id=None, minutes=1440)`.
- `GET /api/aprs/stations`: any authenticated role.
- Frontend: `MessagingCenterWidget`'s APRS tab now shows a compact
  "known stations" pill strip (callsign + lat/lon, hover for last
  info/last-heard time) above the raw packet feed, polled every 10s --
  deduplicated by station, distinct from the packet feed below it
  which shows every packet in arrival order.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 100/100 passing (5 new:
  persist-and-query round trip, second-report-updates-not-duplicates,
  no-position-not-persisted, filter-by-receiver, and a REST-level
  end-to-end test -- same shape as `test_signal_history.py`).
- Frontend: `npm run lint` clean (3 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware**: confirmed `GET /api/aprs/stations` live against
  the running backend (empty list, correctly -- no real APRS position
  packet has been decoded in this environment yet, same known block as
  every other real-decode-verification entry: no guaranteed APRS
  traffic in range of whatever antenna is attached here). The
  persistence logic itself is verified by the real DB-session-backed
  test suite above, same confidence level as `signal_history.py` had
  before its own first real detection.

## Next Steps

1. Actual map/tile rendering for APRS stations (needs a browser to
   build against properly -- `ROADMAP.md`'s Known Environment Blocks).
2. A real position *history* (not just last-known) if a track/
   breadcrumb view is ever wanted.
3. Same environment blocks as ever.

## Added: signal_detections retention/pruning

Closes the "no automatic pruning/retention policy" gap flagged as
Outstanding Work in the signal-history entry above -- that table gets
one row per detection for as long as signal detection runs on any
receiver, unlike `aprs_stations` (upserted, naturally bounded by
distinct callsigns), so it needed an actual retention policy rather
than growing forever in a long-running deployment.

- New `history` config block (`config.example.yaml`):
  `signal_detection_retention_days` (default 30) and
  `prune_interval_hours` (default 24).
- `signal_history.prune_signal_detections(retention_days)`: a plain
  DELETE ... WHERE detected_at < cutoff, returns rows deleted.
- A background `asyncio.create_task` loop in `main.py`'s lifespan
  (`_prune_loop`), started at startup, cancelled cleanly at shutdown
  (`task.cancel()` + awaited under `contextlib.suppress`). Sleeps for
  the full interval *before* its first prune, not after, so a normal
  restart doesn't immediately re-run a prune that likely just ran.
  Runs on a timer rather than per-insert, since a DELETE on every
  single detection would add overhead disproportionate to how rarely
  pruning actually needs to happen.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 101/101 passing (1 new:
  inserts one record 90 days old and one recent, prunes with a
  30-day retention window, confirms only the old one is deleted).
- **Real hardware/process check**: restarted the live backend with
  the new background task wired in, confirmed clean startup (no
  exceptions) and clean shutdown (task cancellation doesn't hang the
  lifespan teardown) via the actual running process, not just the
  test suite's simulated lifespan.

## Next Steps

1. Consider the same "last-seen" pruning for `aprs_stations` eventually
   (stale entries from months-inactive stations linger in the table,
   though the `minutes` query filter already hides them from the
   Messaging Center's "known stations" strip by default).
2. Same environment blocks as ever.

## Added: Triggered recording (Phase 8)

Closes the "Triggered recording" item from Phase 8's Remaining list --
scoped down to reuse two things that already exist rather than
inventing new plumbing: `SignalDetected` events (already emitted once
signal detection is enabled with a `margin_db`) as the trigger source,
and `RecordingService.start`/`stop` as the recording mechanism.

- `services/triggered_recording.py`: `TriggeredRecordingService` --
  `enable(receiver_id, mode, duration_seconds)` arms it,
  `handle_signal_detected` (a single EventBus subscriber, wired in
  `main.py` next to `persist_signal_detected`) starts a recording the
  first time a detection lands for an armed receiver that isn't
  already recording, then auto-stops it after `duration_seconds` via
  a per-receiver `asyncio.create_task`. Deliberately doesn't
  re-arm/extend an in-progress triggered recording on further
  detections during its own window -- a burst of detections (the
  common case: one real signal crossing several FFT frames) would
  otherwise never let it stop; one recording per trigger, capped at
  `duration_seconds`, is the simple version.
- `POST/POST /api/receivers/{id}/triggered-recording/start|stop`.
  Arming with signal detection not yet enabled is not an error --
  the two are independently toggled and can be turned on in either
  order, the trigger just never fires until both are on.
- `capture-health` now also reports `triggered_recording_armed`, same
  "keep the UI honest about backend state" reasoning as the other
  enabled-flags entry above.
- Frontend: `ReceiverCard` gets a "Record on Signal Detection" toggle
  next to Detect Signals, reusing the existing recording-mode select.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 105/105 passing (4 new:
  a full real-detection-starts-and-auto-stops-recording round trip
  against the mock plugin's capture, disarm-stops-new-triggers,
  capture-health reflects armed state, and an auth-required check).
- Frontend: `npm run lint` clean (3 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware, full end-to-end**: tuned the actual RTL2838 to
  100.3MHz, armed triggered recording, enabled signal detection at an
  8dB margin -- a real adjacent-station signal on the real receiver
  triggered a genuine WAV recording within seconds (`0.76s`/`72928
  bytes` at the moment it was observed, still growing). Test recording
  deleted afterward via the real API.

## Next Steps

1. Scheduled recording (Phase 8's other remaining item -- start/stop
   at a wall-clock time rather than on a trigger).
2. A real retrigger/extend policy if triggered recording needs to
   capture a signal longer than one fixed `duration_seconds` window
   in actual field use.
3. Same environment blocks as ever.

## Added: Scheduled recording (Phase 8)

Closes Phase 8's last concrete Remaining item. Same "reuse
`RecordingService`, add only the glue" shape as `triggered_recording.py`
-- here the trigger is a wall-clock timer instead of a `SignalDetected`
event.

- `services/scheduled_recording.py`: `ScheduledRecordingService.schedule`
  creates an in-memory `ScheduledJob` and an `asyncio.create_task` that
  sleeps until `start_at`, starts the recording, sleeps
  `duration_seconds`, then stops it. `cancel(job_id)` works in either
  phase -- cancelling before `start_at` just prevents it from ever
  starting; cancelling while it's already recording actually stops the
  in-progress recording rather than leaving it running forever with
  nothing left to call `stop()` (caught via `except
  asyncio.CancelledError` around the running phase specifically).
  In-memory only, like triggered recording's armed state -- a job is
  lost across a restart. Worth a real persistence + reconciliation
  pass if this becomes something people rely on unattended, not a
  blocker for "schedule one 10 minutes out and leave the tab open."
- `POST /api/receivers/{id}/scheduled-recording`,
  `GET .../scheduled-recordings`, `DELETE /api/scheduled-recordings/{id}`.
- Frontend: `ReceiverCard` gets a compact schedule form (datetime-local
  + duration-seconds inputs) plus a list of upcoming/in-progress jobs
  with per-job Cancel, polled every 5s.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 109/109 passing (4 new:
  real schedule->start->auto-stop round trip against the mock
  plugin's capture, cancel-before-start prevents the recording,
  cancel-while-recording actually stops it, auth-required check).
- Frontend: `npm run lint` clean (3 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware, full end-to-end**: tuned the actual RTL2838 to
  100.3MHz, scheduled a recording 2 seconds out for a 4-second
  duration, polled job status through `pending` -> `recording` ->
  `done`, confirmed a real 312KB/3.26s WAV was produced, then deleted
  it via the real API.

## Next Steps

1. Waterfall recording (Phase 8's remaining item) -- no concrete use
   case identified yet beyond what IQ replay already covers; revisit
   if a specific need comes up rather than building it speculatively.
2. Persist scheduled-recording jobs (currently in-memory) if restart
   survival becomes important.
3. Same environment blocks as ever.

## Added: PPM (crystal) frequency correction (Phase 2: Calibration)

Closes Phase 2's "Calibration" item. Cheap RTL-SDR dongles commonly
have crystal oscillator drift of tens of ppm, which shows up as every
signal being off-frequency by an offset that scales with frequency --
`rtl_sdr` (the underlying command-line tool this project already
shells out to) has built-in support for this via its `-p` flag, so
this is mostly plumbing an existing capability through, the same
shape as gain/bandwidth/sample-rate before it.

- `ReceiverPlugin.set_ppm_correction` (new, optional base method --
  plugins without a correction mechanism can leave it raising
  `NotImplementedError`) and `ReceiverStatus.ppm_correction`.
- `rtl_sdr` plugin: `_DeviceState.ppm_correction` (default 0), passed
  as `-p <ppm>` to the `rtl_sdr` subprocess in `open_iq_stream` when
  non-zero. Same "takes effect on the next capture, not the one
  already running" behavior gain/bandwidth/sample-rate already have --
  device state is only read at process-spawn time.
- `POST /api/receivers/{id}/ppm-correction`; `ReceiverCard` gets a
  "Calibrate" form next to Tune, plus a PPM correction readout in the
  status grid.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 110/110 passing (1 new:
  set via REST, confirm it round-trips through `GET /api/receivers/{id}`).
- Frontend: `npm run lint` clean (3 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware**: set ppm_correction to 15 on the actual RTL2838,
  confirmed it round-tripped via REST, then started a real Listen
  session and confirmed via `ps aux` that the spawned `rtl_sdr`
  process's actual command line included `-p 15` -- not just that the
  API accepted the value, that it reached the hardware capture. Real
  audio still streamed correctly (RMS ~8300-9600) with the correction
  applied. Reset back to 0 afterward.

## Next Steps

1. Same environment blocks as ever -- nothing else concrete queued
   right now; next slice will need a fresh look at `ROADMAP.md`.

## Added: profile-carried margin_db auto-enables signal detection

Closes the specific follow-up flagged in the profile-decoder-auto-enable
entry above: "extend the same auto-enable pattern to signal detection
once profiles have a natural place to carry a margin_db." Added that
field and wired it through, same "only ever turns it on, never off"
reasoning as the APRS/SAME decoder auto-enable.

- `receiver_profiles.margin_db` (new nullable column, migration 0006).
- `apply_profile`: if the applied profile has `margin_db` set, also
  calls `stream_service.enable_signal_detection(receiver_id,
  margin_db, profile.frequency_hz)`.
- Frontend: `ReceiverProfilesPanel`'s create form gets an optional
  "Detect margin (dB)" field; saved profiles show "detect @ NdB" when
  set.

**Real gap hit and fixed along the way**: this app's zero-config
`db_session.create_all()` only creates *missing tables* on startup --
it never alters an existing table, so adding a column to
`receiver_profiles` (an existing table, unlike every previous
migration which added a brand-new table) silently did nothing against
this environment's actual long-lived dev database. First real REST
call after restart failed with `OperationalError: table
receiver_profiles has no column named margin_db`. Fixed by actually
running Alembic against the live DB: `alembic stamp 0005` (the
existing tables already matched migrations 0003-0005, just recorded
under `alembic_version` as still at `0002` since they'd been created
via `create_all` rather than `alembic upgrade` in the first place),
then `alembic upgrade head` to add the column for real. Worth keeping
in mind for any *future* column-on-existing-table change in this
environment -- `create_all()` won't catch it, an explicit
stamp+upgrade will be needed again.

## Verification

- Backend: `ruff check .` clean; `pytest` -- 111/111 passing (1 new:
  create a profile with `margin_db`, apply it, confirm
  `capture-health` reports `signal_detection_enabled: true`).
- Frontend: `npm run lint` clean (3 pre-existing warnings only);
  `tsc -b && vite build` clean.
- **Real hardware**: created a real profile with `margin_db: 10.0`,
  applied it to the actual RTL2838, confirmed `capture-health` flipped
  `signal_detection_enabled` from unset to `true` with no separate
  start call. Cleaned up (stopped detection, deleted the profile).

## Next Steps

1. Same pattern could extend to occupancy tracking too, if a concrete
   need for it comes up.
2. Keep the create_all()-doesn't-alter-existing-tables gap in mind for
   the next schema change to an existing table.
3. Same environment blocks as ever.
