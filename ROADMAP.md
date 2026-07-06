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
- Un-mocking remaining dashboard widgets (Digital Modes -- FT8/DMR need real decoders and, for FT8, HF hardware this environment doesn't have;
  wideband Spectrum Overview needs a sweeping/multi-capture receiver, not just a single RTL-SDR's ~3MHz instant bandwidth) as their backend
  subsystems land. Recordings and Messaging/APRS are already real (see Phase 8/Phase 5 Completed below).

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
- USB hot-plug monitoring (`HotplugMonitor`: polls `ReceiverService.discover()`
  on a timer, emits `ReceiverConnected`/`ReceiverDisconnected` events -- surfaced
  as toasts via `EventToastBridge`)
- Receiver inventory persistence (`receiver_inventory` table: every receiver
  ever seen, survives unplugging and restarts, `GET /api/receivers/inventory`
  flags each as currently `attached` or not -- `ReceiverInventoryPanel` on the
  Receivers page)

Remaining

- SoapySDR detection
- Airspy / SDRplay / HackRF / PlutoSDR / LimeSDR plugins

---

## Receiver Control

Completed

- Frequency, gain, bandwidth, sample rate (lifecycle state, via REST)
- Live IQ sample streaming (`StreamService`, feeding spectrum/audio/decoders/recording)
- Capture health monitoring (`GET /api/receivers/{id}/capture-health`: worker-thread liveness,
  last-read age, subscriber counts -- surfaced in the UI as a "Capture stalled" badge)
- Profiles (see the "Receiver Profiles" section below)
- Calibration (PPM/crystal frequency correction -- `POST /api/receivers/{id}/ppm-correction`,
  passed through to `rtl_sdr -p`; a "Calibrate" control in `ReceiverCard`)

Remaining

Nothing outstanding in this section right now.

---

## Receiver Profiles

Completed

- Built-in "suggested" band presets (FM broadcast, NOAA Weather Radio,
  APRS 2m, Marine VHF ch16, 2m amateur calling, airband guard,
  ADS-B 1090MHz) -- one-click "Add" turns any of them into a real,
  editable/deletable saved profile via the existing create/apply flow.
  All within RTL-SDR tuning range; AIS/HF entries below are listed
  since a preset just means "tune here", not "decode this" -- ADS-B
  decoding is now built (see Completed below), AIS decoding is still
  unbuilt.
- ADS-B (Mode S extended squitter) decoding: `decoders/mode_s.py`
  (CRC-24 validated DF17/18 -> ICAO address + type code, PPM-demodulated
  directly off the raw IQ envelope at native sample rate -- no
  audio-rate decimation, unlike APRS/SAME) plus a "Decode ADS-B" toggle
  on `ReceiverCard`. Needs a genuinely wideband capture (>=2MS/s, tuned
  to 1090MHz) to resolve anything -- verified correct via synthetic
  round-trip tests; no real aircraft message decoded yet in this
  environment (see the diary entry for why that's not conclusively a
  bug). Callsign (BDS 2,0) and position (needs even/odd CPR frame
  pairing) decoding are deliberately not built yet, same "ship the
  achievable subset first" reasoning as APRS's Mic-E gap.
- ADS-B aircraft persistence (`adsb_aircraft` table: last known contact
  + message count per ICAO address, same upsert-on-event shape as
  `aprs_stations` -- `GET /api/adsb/aircraft`, `AdsbAircraftPanel` on
  the Receivers page).
- AIS decoding (161-162MHz VHF, GMSK): `decoders/ais.py` -- HDLC/NRZI
  framing identical to AX.25 (same CRC-16/X-25 FCS, reused directly),
  audio-rate like APRS/SAME (AIS's GMSK baseband is exactly what
  `fm_discriminator` already recovers, just at 9600 baud). Extracts
  message type + MMSI only; full field decoding (position, course,
  speed -- different layouts per message type) deliberately deferred.
  Plus `ais_vessels` persistence (same shape as `adsb_aircraft`) and an
  `AisVesselsPanel`. Verified via synthetic round-trip tests; no real
  vessel decoded yet in this environment (no confirmed marine VHF
  traffic in range here) -- same category as every other real-traffic
  gap in this project.
- Spectrum scanning (`SpectrumScanService`: cycles a receiver through a
  frequency list on a timer via the same `tune` call the manual Tune
  button uses -- `GET/POST .../scan/start|stop|status`, a scan control
  on `ReceiverCard`). Just retunes on a schedule; combining it with
  signal detection/occupancy to flag "busy" frequencies is a UI/caller
  concern, not fused into the scan subsystem itself.

Remaining

- Amateur digital modes beyond APRS (see Phase 5)
- Weather satellite presets (APT/Meteor-M2 downlink decoding, Phase 7)
- HF monitoring (outside RTL-SDR's tuning range without an upconverter)

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
- Signal history (`SignalDetectionRecord` DB table, survives restarts, queryable via `GET /api/receivers/{id}/signal-history`, pruned on a configurable retention schedule -- `history.signal_detection_retention_days`/`prune_interval_hours`)

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

Completed

- Pass prediction (`satellite_passes.py`: real SGP4 propagation via the
  `sgp4` library -- the industry-standard implementation, not
  hand-derived -- plus a spherical-Earth/GMST-only topocentric az/el
  model, accurate for pass timing to within roughly a minute.
  `POST /api/satellites/passes`; a `/satellites` page with a TLE +
  ground-station form. Callers supply their own current TLE (e.g. from
  Celestrak) -- none is bundled/fetched, since a shipped TLE would be
  stale within 1-2 weeks.)
- Automatic recording (`POST /api/satellites/{receiver_id}/schedule-next-pass`:
  finds the next pass and schedules a recording covering it exactly,
  reusing `ScheduledRecordingService` -- optionally tunes the receiver
  to the satellite's downlink frequency immediately, since the
  scheduler itself just records whatever the receiver is already on.
  A "Schedule Recording for Next Pass" control on `/satellites`.)
- TLE auto-fetch (`services/n2yo.py`: fetches a current TLE by NORAD
  catalog number from n2yo.com's free, registration-required API --
  `GET /api/satellites/tle/{norad_id}`, needs `satellites.n2yo_api_key`
  configured or 400s with a clear message pointing at
  n2yo.com/api. A "Fetch by NORAD ID" control on `/satellites` next to
  manual TLE paste, which still always works. Live-verified with a
  real API key: fetched NOAA 15's real TLE and predicted the same
  pass schedule an independent Celestrak-sourced TLE had already
  produced.)

Remaining

- Tracking (retuning across a pass to follow Doppler shift)
- Scheduling (recurring/multi-satellite scheduling beyond "next pass")

---

# Phase 8 — Recording

Completed

- Audio recording (WAV, FM/AM demodulated -- `RecordingService`)
- IQ recording (raw `.iq` + sample-rate sidecar)
- Replay (`.iq` recordings play back through the real spectrum/audio/decoder
  pipeline via `StreamService.register_playback` -- see `RecordingsWidget`)
- Recording management (list/download/delete via `GET/DELETE /api/recordings`,
  `RecordingsWidget`)
- Triggered recording ("record when signal detected" -- `TriggeredRecordingService`
  arms a receiver to auto-record for a fixed duration on the next `SignalDetected` event)
- Scheduled recording (start/stop at a wall-clock time -- `ScheduledRecordingService`,
  in-memory only: a job is lost if the backend restarts before it fires)

Remaining

- Waterfall recording (a saved spectrogram/FFT-frame capture, distinct from
  raw IQ -- no concrete use case identified yet beyond what IQ replay already covers)
- Persisting scheduled recording jobs across a restart (currently in-memory only)

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
- Actual map/tile rendering: see **Phase 17 — Geospatial Intelligence**,
  which absorbs and supersedes this phase's map-rendering "Remaining"
  items below. The position-*decoding* work above stays credited here;
  the map/layer implementation itself is tracked in Phase 17.

Remaining

- APRS Mic-E position format (needs real captured packets to verify
  against, not a from-memory table transcription)
- Everything else map-related is now tracked under Phase 17

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

# Phase 17 — Geospatial Intelligence

A platform capability, not a single map page -- see `ARCHITECTURE.md`'s
"Geospatial Intelligence Platform" section for the full design (the
`MapLayer` interface, self-registering layers, provider abstraction,
tile-provider swapping). This phase absorbs and supersedes Phase 9's
"Remaining" map-rendering items (the position-*decoding* work Phase 9
already did -- APRS position parsing/persistence -- stays credited
there; the actual map/layer implementation is tracked here).

Framework choices: **Leaflet** + free OSM-derived tiles (CartoDB Dark
Matter by default, standard OSM as an alternative) -- mature, free, no
vendor lock-in, plugin-rich, works with zero API keys out of the box.
**satellite.js** (pinned to 6.0.2, the pure-JS release -- see
`ARCHITECTURE.md` for why 7.x's WASM build doesn't currently bundle
for the browser) for client-side SGP4/SDP4; the backend only ever
distributes TLE data, never computes a position itself.

## Interactive Map Engine

Completed

- `GeospatialPage` (`/map`): full-screen Leaflet map, dark theme
  (CartoDB Dark Matter default), swappable base tile provider, scale
  control, default Leaflet zoom control, live mouse lat/lon readout,
  per-layer enable/disable sidebar with a "live" indicator dot for
  auto-refreshing layers.

Remaining

- Place-name search (a coordinate-jump box would be the minimal first
  step; full geocoding needs a provider -- Nominatim, OSM's own free
  option, is the natural candidate, rate-limited but keyless)
- Provider status/health indicator beyond the per-layer "live" dot
  (a real health model -- last successful fetch, error state per
  layer/provider -- once there are enough external providers for it
  to matter)

## Layer Framework

Completed

- `MapLayer` interface + self-registering `LayerRegistry`
  (`frontend/src/geo/`) -- the map/page depend only on the interface,
  never a concrete layer. See `ARCHITECTURE.md` for the full contract.

Remaining

- Nothing concrete -- the framework is considered done until a real
  new layer's needs prove otherwise (e.g. a shared per-layer health/
  status model, if enough providers accumulate to need one).

## Satellite Intelligence

Completed

- Ground track + current-position layer (`SatelliteTrackLayer`),
  computed entirely client-side via `satellite.js` from a TLE fetched
  through the existing `GET /api/satellites/tle/{norad_id}` (n2yo.com)
  or pasted manually.
- (Already built in Phase 9/the Satellites page, reused here rather
  than duplicated: pass prediction, schedule-recording-for-next-pass.)

Remaining

- Multiple simultaneously-tracked satellites (currently one at a time)
- CelesTrak as a bulk/alternative TLE source (useful for "show me
  every Starlink" style layers n2yo's per-satellite lookup doesn't fit
  well) -- would follow the same provider-adapter shape as
  `services/n2yo.py`
- Visual-pass/horizon/Doppler overlays beyond ground track + position

## Space Weather

Remaining (nothing built yet)

- NOAA SWPC provider adapter (Kp index, solar wind, X-ray/proton flux,
  geomagnetic storms, CME alerts, radio blackouts, HF fadeouts)
- Aurora oval / probability / forecast overlays
- Designed to allow additional sources to supplement NOAA later
  (provider-abstraction shape, not a NOAA-specific integration)

## Weather Layers

Remaining (nothing built yet)

- NEXRAD, GOES imagery, storm polygons, lightning detection

## APRS

Completed

- Station layer (see Layer Framework above), backed by the existing
  `aprs_stations` persistence layer (Phase 9).

Remaining

- Symbol-accurate map icons (currently a plain circle marker for every
  station regardless of APRS symbol table/code)
- Track/breadcrumb history per station (currently last-known-position
  only, same gap noted in the Phase 9 diary entries)

## ADS-B

Remaining (blocked on position decoding, not the layer framework)

- Aircraft layer needs real lat/lon, which needs CPR (compact position
  reporting) frame-pairing decoding -- deliberately deferred when the
  Mode S decoder was built (see the ADS-B diary entry). The framework
  itself doesn't block this; it's a decoder gap, not a mapping one.

## AIS

Remaining (blocked on position decoding, not the layer framework)

- Same shape of gap as ADS-B: the AIS decoder currently extracts
  message type + MMSI only, not position (see the AIS diary entry).

## RF Coverage

Remaining (nothing built yet)

- Coverage/propagation modeling per receiver site -- blocked on
  receivers having a stored site location at all (they don't yet;
  receiver inventory tracks "seen", not "located").

## Heat Maps

Remaining (nothing built yet)

- Signal-detection-density or occupancy-density overlays -- the
  underlying data (`signal_detections` table, `OccupancyTracker`)
  already exists; this is a new layer consuming existing data, not a
  new backend subsystem.

## Historical Playback

Remaining (nothing built yet)

- Time-scrubbing across persisted history (`signal_detections`,
  `aprs_stations`, `adsb_aircraft`/`ais_vessels` once those have
  position) -- a real "historical" layer needs point-in-time queries
  those tables don't currently expose (they only return current/
  recent state).

## Alerts

Remaining (nothing built yet)

- Geospatial alerting (e.g. "notify when an APRS station enters a
  drawn boundary") -- natural fit for `ToastContext`/`EventToastBridge`
  once there's a geospatial trigger condition to evaluate.

## Mobile Support

Remaining (nothing built yet, and unverifiable in this environment
regardless -- no browser/mobile device available here; see
`ARCHITECTURE.md`/known environment blocks).

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