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

**Implementation note:** SQLAlchemy 2.0 async ORM (`aiosqlite` driver).
Alembic (`backend/alembic/`) is wired up and holds the initial schema
revision, but the running app currently calls `Base.metadata.create_all`
on startup for a zero-configuration first run; Alembic becomes the
enforced path once the schema needs real migrations rather than a
single `users` table.

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

**Implementation note:** the interface actually implemented in
`backend/app/plugins/receiver.py` refines the sketch below so a single
plugin instance can manage more than one physical device (e.g. several
RTL-SDR dongles) -- lifecycle methods take an explicit `receiver_id`:

```python
class ReceiverPlugin(Plugin):
    def discover(self) -> list[ReceiverDescriptor]: ...
    def start(self, receiver_id: str) -> ReceiverStatus: ...
    def stop(self, receiver_id: str) -> ReceiverStatus: ...
    def tune(self, receiver_id: str, frequency_hz: int) -> ReceiverStatus: ...
    def set_gain(self, receiver_id: str, gain: str | float) -> ReceiverStatus: ...
    def set_bandwidth(self, receiver_id: str, bandwidth_hz: int) -> ReceiverStatus: ...
    def set_sample_rate(self, receiver_id: str, sample_rate_hz: int) -> ReceiverStatus: ...
    def device_status(self, receiver_id: str) -> ReceiverStatus: ...
```

`device_status` (not `status`) is deliberate: the base `Plugin.status()`
is a no-argument, plugin-level health probe used generically by
`GET /api/plugins`, and a receiver's per-device status is a distinct
concept with a different signature. See `docs/PLUGIN_API.md` for the
full contract and the base `Plugin`/`RadioPlugin`/`DecoderPlugin`/
`DashboardPlugin`/`AutomationPlugin` interfaces (the latter four are
defined but not yet wired to a manager -- see ROADMAP.md).

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

**Implementation note:** `backend/app/core/config.py` layers these
sources with the following precedence (highest first): explicit
constructor kwargs (tests) > `ECHO_BASE_*` environment variables
(nested via `__`, e.g. `ECHO_BASE_SERVER__PORT`) > `config/config.yaml`
> built-in defaults. Nothing is required to boot; see
`config/config.example.yaml`.

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

**Implementation note:** authentication is a signed JWT stored in an
httponly session cookie (`echo_base_session`), also accepted as a
`Bearer` token for non-browser clients. Passwords are hashed with
bcrypt. A fresh install with no users auto-creates an `admin` account
with a random password printed once to the console/log and a forced
`must_change_password` flag -- there is no setup wizard yet (tracked in
ROADMAP.md). Every response uses the standard envelope from
`docs/REST_API.md` (`{success, data}` / `{success: false, error}`),
enforced centrally via FastAPI exception handlers in `app/main.py`.

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

# Geospatial Intelligence Platform

A first-class subsystem, not a single map page. The design goal is the
same one the plugin architecture already applies to receivers/radios/
decoders: a stable interface that lets new data sources be added
without touching the map, the page, or any other layer.

## Overall design

```
                  GeospatialPage (frontend/src/pages/GeospatialPage.tsx)
                            │
                     Leaflet L.Map instance
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        MapLayer      MapLayer      MapLayer  ...  (LayerRegistry)
      (APRS Stations) (Satellite    (future: AIS,
                        Ground       ADS-B, RF
                        Track)       coverage, ...)
              │             │
      GET /api/aprs/    satellite.js
        stations        (client-side SGP4,
      (existing REST    fed by
       endpoint,        GET /api/satellites/tle/{norad_id})
       Phase 9)
```

The page owns exactly one thing every layer needs: a live `L.Map`
instance and a place to put a sidebar toggle. It has no knowledge of
what a layer draws, how often it refreshes, or where its data comes
from -- that isolation is the entire point, and it's what lets a
future RF-coverage or AIS layer be added as a new file plus one import
line, not a change to the map page.

## The `MapLayer` interface

Every layer (`frontend/src/geo/types.ts`) implements:

```typescript
interface MapLayer {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly defaultEnabled: boolean;

  initialize(map: L.Map): void | Promise<void>;
  refresh(): void | Promise<void>;
  enable(): void;
  disable(): void;
  destroy(): void;
}
```

`initialize` is called once per page load with a live map instance.
`enable`/`disable` add/remove the layer's Leaflet objects from the map
without discarding state (toggling a layer off and back on doesn't
re-fetch). `destroy` is the only place a layer's timers/subscriptions
actually get torn down, called on unmount.

## Layer registry (self-registering layers)

`frontend/src/geo/LayerRegistry.ts` is a flat list of factory
functions. A layer module calls `registerLayer(() => new MyLayer())`
as a side effect of being imported; `frontend/src/geo/layers/index.ts`
imports every layer module and nothing else. Adding a layer is:

1. Write a class implementing `MapLayer` in `geo/layers/`.
2. Add one `import "./MyLayer";` line to `geo/layers/index.ts`.

`GeospatialPage` calls `createRegisteredLayers()` once and never
imports a concrete layer class directly (the one deliberate exception
is `SatelliteTrackLayer`, whose extra `setSatellite()` method the
page's satellite-picker control needs -- see "Layer-specific
extensions" below).

## Provider abstraction (backend)

The frontend never calls an external data provider directly -- every
external service is isolated behind a backend service module that
downloads, validates, and normalizes data before it reaches a REST
endpoint:

- `services/aprs_stations.py` -- not an external provider, but same
  shape: normalizes decoded `AprsPacket` events into a queryable
  "last known position per station" table.
- `services/satellite_passes.py` -- wraps the `sgp4` library (not an
  external network call; the actual propagation library).
- `services/n2yo.py` -- isolates n2yo.com's HTTP API (including its
  own quirks, like returning HTTP 200 with a malformed body for some
  bad requests) behind a clean `fetch_tle()` call that raises a real
  `N2yoError` instead of letting a provider-specific failure mode leak
  upward.
- `services/noaa_swpc.py` -- the second external-provider adapter,
  proving the pattern generalizes to a provider with a very different
  data shape (a real-time scalar time series for Kp, a 65k-point
  global grid for aurora) without changing anything about `n2yo.py` or
  the layers that don't consume space weather. Also demonstrates the
  "normalize before it reaches the frontend" rule at its most literal:
  NOAA's aurora grid is rendered to a single PNG server-side
  (`render_aurora_png`) rather than shipping 65,160 raw points to the
  browser to turn into a comparable number of Leaflet objects.

Adding a new external provider (e.g. CelesTrak as an alternative bulk
TLE source alongside n2yo, or a second space-weather source alongside
NOAA) means adding one new service module with the same shape --
fetch, validate, normalize, expose via REST -- not changing any
existing provider's code or any frontend layer that doesn't consume
it.

## Provider caching and graceful failure (the general pattern)

Every provider adapter with a real "fetch from the internet
periodically" shape follows the same structure, first established by
`HotplugMonitor` and generalized by `SpaceWeatherService`:

1. A stateful service class holds the last-successfully-fetched data
   in memory (`SpaceWeatherService._kp_readings`/`_aurora_png`, etc.).
2. A `refresh_*()` method fetches, and **only replaces the cached data
   on success** -- a failure is logged and the previous data (however
   old) stays in place. A REST endpoint reading from this cache never
   itself talks to the external provider, so a slow/down provider
   can't turn into a slow/down Echo Base endpoint.
3. A background `asyncio` task (`_periodic_refresh_loop` in
   `main.py`, wired into the app lifespan alongside `HotplugMonitor`/
   the signal-detection pruning task) calls `refresh_*()` once
   immediately at startup (so data exists before the first interval
   elapses) and then on a configurable interval (`SpaceWeatherSettings`
   in `core/config.py` -- same shape as `HotplugSettings`/
   `HistorySettings`).
4. The REST endpoint 404s only in the narrow window before the very
   first refresh completes; after that, it always returns *something*,
   even if every subsequent refresh has failed.

This is the template for any future "fetch periodically from an
external source" provider (space weather's remaining datasets, a
future weather-radar/NEXRAD layer, etc.) -- not something to redesign
per provider.

## Orbit calculations happen in the browser, not the backend

`SatelliteTrackLayer` is the one layer whose "provider" is a pure
computation rather than a fetched dataset: it takes a TLE (fetched via
`GET /api/satellites/tle/{norad_id}`, or pasted manually on the
Satellites page) and runs `satellite.js` (SGP4/SDP4) directly in the
browser to compute current position and a ground track. The backend's
job stops at distributing TLE data -- it never computes a satellite
position itself. This keeps the backend's satellite-related surface
area small (fetch/cache/validate a TLE) and keeps orbit math where
it's cheapest to run per-client (a ground track redraws every few
seconds while a pass is being watched; that's client CPU, not a
server request).

**Dependency note:** `satellite.js` is pinned to `6.0.2` (not the
latest `7.x`) -- 7.x bundles an optional WebAssembly-accelerated SGP4
path that Vite/Rollup can't currently bundle for the browser (it pulls
in Node-only modules and top-level `await` in an IIFE chunk). 6.0.2 is
the pure-JS implementation with no such build issue, and is more than
fast enough for one satellite's ground track recomputed every few
seconds.

## Layer-specific extensions

Not every layer's configuration fits the common interface (there's no
generic "target" concept every layer shares) -- `SatelliteTrackLayer`
exposes `setSatellite(name, tleLine1, tleLine2)` and `clearSatellite()`
beyond `MapLayer`. `GeospatialPage`'s satellite-picker control looks up
that specific layer instance by `id` and calls the extra method on it,
typed via the concrete class rather than the interface. This is a
deliberate, narrow exception: the `MapLayer` interface covers what the
*map* needs from every layer; a layer's own configuration surface is
its own business, reached only by code that already knows it's dealing
with that specific layer (never by the map itself).

## Tile provider abstraction

The base map tiles are also swappable without touching
`GeospatialPage`: `frontend/src/geo/tileProviders.ts` is a small list
of `{id, name, url, attribution, maxZoom}` entries. Both current
entries (CartoDB Dark Matter, standard OpenStreetMap) are free,
OSM-derived, and need no API key -- a deliberate constraint so the map
works out of the box with zero configuration. Adding a provider that
needs a key (a commercial tile host, say) later is one new entry in
that list.

## Caching and update intervals

Each layer manages its own refresh cadence independently (no shared
scheduler yet):

- **APRS Stations**: polls `GET /api/aprs/stations` every 15s. The
  underlying data is already cached server-side (the `aprs_stations`
  table, upserted on every decoded packet) -- this is a display-refresh
  interval, not a fetch-from-external-provider interval.
- **Satellite Ground Track**: recomputes every 5s locally (no network
  call at all once a TLE has been loaded -- `satellite.js` runs
  entirely client-side).

Future providers with a real "fetch from the internet periodically"
shape (NOAA SWPC space weather, CelesTrak bulk TLE catalogs) should
follow the pattern already established by `HotplugMonitor` and the
signal-detection pruning task in `main.py`'s lifespan: a background
`asyncio` task on a configurable interval (see `HotplugSettings`/
`HistorySettings` in `core/config.py` for the existing shape), writing
into a local cache table, with REST endpoints serving the cache and
falling back to the last-known-good data if a provider fetch fails
rather than erroring the whole endpoint out.

## What's built vs. what the framework merely supports

Six real layers exist today: **APRS Stations** (backed by data this
project already decodes and persists), **Satellite Ground Track**
(backed by TLE data this project already fetches/predicts passes
from), **Aurora Forecast** (backed by NOAA SWPC, rendered
server-side to a PNG), **Receiver Sites** (backed by an
operator-set location on `receiver_inventory` -- deliberately never
inferred, since a plain RTL-SDR dongle has no GPS; set via
`PUT /api/receivers/{id}/location`, requiring the receiver to have
been seen at least once), **ADS-B Aircraft** (backed by real CPR
position decoding -- `decoders/adsb_position.py` pairs even/odd
Compact Position Reporting frames per ICAO address and resolves a real
lat/lon, verified against the standard published reference decode
example and a full synthetic-waveform round-trip; default-off since it
needs an active wideband 1090MHz capture to show anything), and **FT8
Stations** (backed by a from-scratch FT8 receiver --
`decoders/ft8_decoder.py` -- positioned at each decoded station's grid
square centroid; verified against a real off-air recording with
independently-published ground truth, not just synthetic; default-off
since it needs an active HF/USB capture). Every other layer described
in `ROADMAP.md`'s Geospatial Intelligence phase -- AIS ships, RF
coverage/heat maps, storm polygons -- is a real gap in *data*, not in
the layer framework: AIS position decoding remains deliberately
deferred (see the diary). The framework itself places no constraint on
adding any of them; each is exactly the same shape of work as APRS
Stations/Aurora Forecast/Receiver Sites/ADS-B Aircraft/FT8 Stations
were (a backend data source + a `MapLayer` subclass + one import
line).

## Future extensibility

Adding a genuinely new layer requires, at most:

1. A backend service/route if the data doesn't already have one
   (following the provider-abstraction shape above).
2. A `MapLayer` subclass in `frontend/src/geo/layers/`.
3. One import line in `geo/layers/index.ts`.

No changes to `GeospatialPage`, `LayerRegistry`, or any other layer.
The same reasoning extends to swapping the mapping library itself
(Leaflet was chosen for being free, mature, plugin-rich, and
OSM-native -- see `ROADMAP.md`'s Geospatial Intelligence phase for the
full reasoning) -- every layer talks to the map only through the
`MapLayer` interface's `initialize(map: L.Map)` parameter, so replacing
Leaflet would mean rewriting layer internals but not the registration/
toggle/lifecycle model around them.

---

# Decoder Registry (frontend) -- decoders are pointed at receivers, not owned by them

`ReceiverCard.tsx` originally grew a hardcoded button (and, for SSTV,
an inline image panel) for every protocol decoder as they were added --
APRS, SAME, ADS-B, AIS, SSTV, FT8 -- until the card became a wall of
buttons most of which were irrelevant to whatever the receiver
happened to be tuned to. A first pass fixed the clutter with a
self-registering `DecoderRegistry` (mirroring the Geospatial map's
`MapLayer`/`LayerRegistry`) but kept the same *ownership direction*:
the receiver still hosted the decoder.

That direction was backwards, and was corrected on direct feedback:
**a decoder is an independent, addressable unit that gets pointed at
whichever receiver you choose** -- the same relationship SDRAngel's
device/channel model has (a "channel" plugin like an NFM demodulator
is configured independently and assigned to a device, not baked into
the device's own UI). `ReceiverCard` went back to being only about the
receiver itself (tune/gain/scan/recording/start-stop); decoders moved
to their own page (`/digital-modes`, `DigitalModesPage.tsx`), each
rendered as an independent `DecoderPanel` that owns a receiver
*selection*, not the other way around.

## The `DecoderDefinition` interface

```ts
interface DecoderDefinition {
  id: string;
  name: string;
  description: string;
  bands: FrequencyBand[];      // where this decoder is meant to be used
  healthKey: keyof CaptureHealth; // which capture-health field reflects it
  start: (receiverId: string) => Promise<unknown>;
  stop: (receiverId: string) => Promise<unknown>;
  feedsMapLayer?: string;      // the geo/layers MapLayer id it populates, if any
  Panel?: ComponentType<{ receiverId: string }>; // the decoder's live data view
}
```

Unchanged from the first pass -- the registry itself
(`decoders/DecoderRegistry.ts`) and the self-registration convention
(one file per decoder in `frontend/src/decoders/`, imported for its
side effect in `decoders/index.ts`) were sound; only the *consumer* of
the registry moved.

## `DecoderPanel` -- a decoder's own receiver selector, not the receiver's own decoder list

`decoders/DecoderPanel.tsx` is rendered once per registered decoder on
`DigitalModesPage`. Each instance:

- Has its own receiver-select dropdown (populated from `GET
  /api/receivers`), independent of every other decoder panel.
- Remembers its receiver assignment per decoder id in `localStorage`,
  so reloading the page reconnects each panel to whatever it was last
  pointed at -- "switching between panels, each listening within its
  own config" is the intended normal usage, not a special case.
- Polls `GET .../capture-health` and `GET /api/receivers/{id}` for
  *its selected receiver only* (not a shared poll -- each panel is
  independently addressable, so there's no single "the" receiver to
  share state from) to derive its own enabled state and the
  receiver's current tuning.
- Renders the decoder's `Panel` (its live data view -- a station/
  aircraft/vessel table, or SSTV's progressively-decoding image) below
  its own controls, passing down whichever receiver it's currently
  pointed at.

## Frequency-band awareness -- a real "relates to" link, not just a filter

Each decoder declares the frequency range(s) it's meant for (e.g. ADS-B
near 1090MHz, FT8 across its ~11 standard HF dial frequencies, SSTV
across several VHF/HF calling frequencies). `DecoderPanel` compares
these against its selected receiver's current tuning and visually
de-emphasizes (not hides -- an already-running decoder should never
look like it vanished just because the receiver got retuned) its own
Start/Stop control when out of band, with a tooltip explaining why.

`feedsMapLayer` is the other half of "components that relate and
chain": a decoder can name the `geo/layers` `MapLayer` id its real data
populates (e.g. FT8's decoder names `"ft8-stations"`), so the panel can
tell the user "this also lights up the map" instead of the decoder and
the map layer being two silently unrelated pieces of UI that happen to
share a backend.

## Existing per-receiver/per-protocol components stayed dual-use

`AdsbAircraftPanel`/`AisVesselsPanel` (originally global, receiver-
agnostic summaries on the Receivers page) gained an optional
`receiverId` prop rather than being duplicated: given one, they filter
to that receiver and skip their own `Card` chrome (the wrapping
`DecoderPanel` already supplies it); omitted, they behave exactly as
before. `Ft8StationsPanel`/`AprsStationsPanel` are new, built directly
against the `DecoderPanelProps` shape since no prior global widget for
them existed.

## Future extensibility

Adding a new decoder requires, at most:

1. The backend route/toggle if it doesn't already exist.
2. A `DecoderDefinition` file in `frontend/src/decoders/` (with a
   `Panel` component for its live data view, if it has one).
3. One import line in `decoders/index.ts`.

No changes to `DigitalModesPage`, `DecoderPanel`, `ReceiverCard`, or
any other decoder -- the same shape of extensibility guarantee
`MapLayer` gives the Geospatial platform.

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