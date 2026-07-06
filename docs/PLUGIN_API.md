# Echo Base Plugin API

> **Version:** 0.1.0 (Draft)

Echo Base is designed around a plugin-first architecture.

Rather than embedding support for every SDR, radio, decoder, or messaging protocol directly into the core platform, Echo Base provides a common plugin framework that allows new functionality to be added without modifying the core application.

The long-term objective is for **every major subsystem** to be extensible through plugins.

---

# Design Goals

The Plugin API is designed to provide:

- Loose coupling
- Hardware abstraction
- Runtime discovery
- Hot loading (future)
- Version compatibility
- Stable interfaces
- Independent development
- Third-party extensibility

Plugins should never directly modify the Echo Base core.

All communication occurs through defined APIs and events.

---

# Plugin Categories

Echo Base supports multiple plugin types.

## Hardware

Hardware plugins provide access to physical devices.

Examples:

- RTL-SDR
- Airspy
- SDRplay
- HackRF
- LimeSDR
- PlutoSDR

---

## Radio

Radio plugins provide control of transceivers.

Examples:

- Hamlib
- CAT
- Icom CI-V
- Kenwood CAT
- Yaesu CAT
- FlexRadio API

---

## Decoder

Decoder plugins integrate external software.

Examples:

- dump1090
- readsb
- rtl_433
- Dire Wolf
- JS8Call
- WSJT-X
- FLDIGI
- SatDump

---

## Messaging

Messaging plugins expose communications systems.

Examples:

- APRS
- Winlink
- Packet
- JS8 Messaging
- MQTT

---

## Dashboard

Dashboard plugins contribute user interface components.

Examples:

- Maps
- Waterfalls
- Aircraft displays
- Weather panels
- Statistics
- Gauges

---

## Recording

Recording plugins provide storage engines.

Examples:

- IQ recording
- Audio recording
- Cloud storage
- Compression
- Archive management

---

## Automation

Automation plugins provide actions and triggers.

Examples:

- Webhooks
- MQTT
- Scripts
- Email
- Discord
- Matrix

---

## AI

Future AI plugins may include:

- Signal classification
- Decoder recommendation
- Signal clustering
- Occupancy analysis
- Natural language search

---

# Plugin Directory Structure

Example:

```
plugins/

    rtl_sdr/
        plugin.py
        manifest.yaml
        requirements.txt

    airspy/
        plugin.py
        manifest.yaml

    direwolf/
        plugin.py

    js8call/
        plugin.py
```

---

# Manifest

Every plugin includes a manifest.

Example:

```yaml
name: RTL-SDR

id: rtl_sdr

version: 1.0.0

author: Example Developer

description: RTL-SDR receiver support

plugin_type: receiver

api_version: 1

entry_point: plugin.py
```

---

# Base Plugin Interface

Every plugin derives from the base class.

```python
class Plugin:

    def initialize(self):
        """Called when the plugin loads."""

    def shutdown(self):
        """Called before unloading."""

    def status(self):
        """Return current plugin status."""
```

---

# Receiver Plugin Interface

Receiver plugins expose SDR hardware.

```python
class ReceiverPlugin(Plugin):

    def discover(self):
        """Return discovered receivers."""

    def start(self):
        """Start receiver."""

    def stop(self):
        """Stop receiver."""

    def tune(self, frequency):

        pass

    def set_gain(self, gain):

        pass

    def set_bandwidth(self, bandwidth):

        pass

    def set_sample_rate(self, rate):

        pass

    def status(self):

        pass
```

---

# Radio Plugin Interface

```python
class RadioPlugin(Plugin):

    def connect(self):

        pass

    def disconnect(self):

        pass

    def frequency(self):

        pass

    def set_frequency(self, hz):

        pass

    def mode(self):

        pass

    def set_mode(self, mode):

        pass

    def ptt(self, state):

        pass

    def status(self):

        pass
```

---

# Decoder Plugin Interface

```python
class DecoderPlugin(Plugin):

    def start(self):

        pass

    def stop(self):

        pass

    def configure(self, config):

        pass

    def statistics(self):

        pass
```

---

# Dashboard Plugin Interface

Dashboard plugins contribute user interface components.

```python
class DashboardPlugin(Plugin):

    def routes(self):

        pass

    def widgets(self):

        pass

    def menu_items(self):

        pass
```

---

# Automation Plugin Interface

```python
class AutomationPlugin(Plugin):

    def triggers(self):

        pass

    def actions(self):

        pass
```

---

# Events

Plugins communicate through the Event Bus.

Examples:

```
ReceiverStarted

ReceiverStopped

ReceiverError

SignalDetected

SignalLost

RecordingStarted

RecordingStopped

RecordingCompleted

AircraftDetected

AISContact

WeatherAlert

SatellitePassStarted

SatellitePassEnded

MessageReceived

MessageSent

AlertGenerated

SystemHealthChanged
```

Plugins should publish events rather than calling other plugins directly.

---

# REST API Integration

Plugins may expose REST endpoints.

Example:

```
GET

/api/plugins

GET

/api/plugins/{id}

POST

/api/plugins/{id}/reload

POST

/api/plugins/{id}/configure
```

Plugins should register routes during initialization.

---

# WebSocket Integration

Plugins may publish live updates.

Examples:

```
Receiver status

Signal activity

Messages

Aircraft

AIS

Waterfalls

Spectrum updates

Alerts
```

The frontend subscribes through the Echo Base event stream.

---

# Configuration

Every plugin receives a configuration object.

Example:

```yaml
plugins:

  rtl_sdr:

    gain: auto

    ppm: 0

    serial: "00000001"
```

Plugins should never modify global configuration directly.

---

# Logging

Plugins receive a logger from the framework.

Example:

```python
logger.info("Receiver started.")

logger.warning("High CPU usage.")

logger.error("Device disconnected.")
```

Plugins should never print directly to stdout.

---

# Dependencies

Plugins may define dependencies.

Example:

```
Python packages

External executables

Shared libraries

Kernel drivers
```

Echo Base will eventually validate these during installation.

---

# Security

Plugins execute with the permissions of the Echo Base service.

Plugins should:

- Validate all input
- Handle errors gracefully
- Never expose secrets
- Never execute arbitrary shell commands without sanitization

Future versions may support plugin sandboxing.

---

# Versioning

Every plugin declares:

```
Plugin Version

API Version

Minimum Echo Base Version

Maximum Tested Version
```

This allows compatibility validation during startup.

---

# Distribution

Future versions of Echo Base may include a plugin registry.

Possible installation methods:

```
echo plugins install rtl_sdr

echo plugins update

echo plugins remove

echo plugins search
```

Third-party repositories may also be supported.

---

# Best Practices

Plugin authors should:

- Keep plugins focused on a single responsibility.
- Reuse common framework services.
- Publish events instead of directly calling other plugins.
- Document configuration options.
- Handle hardware failures gracefully.
- Log meaningful operational information.
- Avoid blocking the event loop.
- Write unit tests when practical.

---

# Future Enhancements

The Plugin API is expected to evolve to support:

- Hot plugin loading
- Automatic updates
- Dependency resolution
- Digital signatures
- Sandboxed execution
- Remote plugins
- Plugin marketplace
- Plugin health monitoring
- Performance metrics

---

# Philosophy

Echo Base is intended to become a platform rather than a monolithic application.

The Plugin API is the foundation that enables that vision.

Whenever possible, new functionality should be implemented as a plugin instead of modifying the core system.

A healthy plugin ecosystem will allow Echo Base to support new radios, SDRs, digital modes, automation systems, and emerging technologies without requiring changes to the platform itself.