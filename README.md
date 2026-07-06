# Echo Base

> **An Open-Source Radio Operations Platform**

Echo Base is an open-source platform for building a centralized radio operations center on Linux.

Rather than acting as a single SDR application or radio program, Echo Base provides a unified command and control platform capable of managing Software Defined Radios (SDRs), conventional transceivers, digital mode applications, messaging systems, spectrum monitoring, recording, automation, and radio intelligence through a modern web interface.

The goal is simple:

> **Turn a collection of radios into an integrated communications and spectrum operations center.**

---

# Vision

Modern radio operators often run numerous independent applications simultaneously:

- SDR software
- APRS software
- ADS-B decoders
- AIS receivers
- Winlink
- JS8Call
- FLDIGI
- WSJT-X
- Packet radio
- Weather satellite decoders
- Logging software
- Recording tools

Each application solves a specific problem, but there is no unified platform that brings them together into a cohesive operational environment.

Echo Base aims to become that platform.

---

# Core Objectives

- Centralized radio management
- Multi-SDR support
- Transceiver control
- Digital mode integration
- Communications management
- Spectrum intelligence
- Recording and playback
- Automation and alerting
- Distributed receiver support
- Plugin architecture
- Modern web-based operations center

---

# Features (Planned)

## SDR Management

- Multiple RTL-SDR receivers
- Airspy support
- SDRplay support
- HackRF support
- LimeSDR support
- PlutoSDR support
- SoapySDR integration
- Receiver grouping
- Remote SDR support

---

## Radio Control

Control supported amateur and commercial radios through:

- Hamlib
- rigctld
- CAT interfaces
- USB Serial
- Network APIs
- GPIO/PTT interfaces

Supported functionality will vary by radio model.

---

## Spectrum Monitoring

- Live spectrum displays
- Waterfalls
- Frequency occupancy
- Signal history
- Band utilization
- RF heatmaps
- Receiver health
- Spectrum recording

---

## Digital Modes

Integration with existing applications including:

- APRS
- Packet Radio
- Winlink
- JS8Call
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

Echo Base orchestrates these applications rather than replacing them.

---

## Aviation

- ADS-B
- UAT 978
- ACARS
- VDL2

Live aircraft mapping and historical playback.

---

## Marine

- AIS
- Marine VHF monitoring

---

## Weather

- NOAA Weather Radio
- SAME Alerts
- NOAA APT
- Meteor-M2
- GOES support (future)

---

## Satellite

- Pass prediction
- Automatic recording
- Satellite scheduling
- Telemetry collection

---

## Messaging

Unified messaging dashboard for:

- APRS
- Winlink
- JS8
- Packet
- Digital chat systems

---

## Recording

Record:

- IQ streams
- Audio
- Waterfalls
- Events
- Scheduled recordings
- Triggered recordings

Replay any captured transmission through the web interface.

---

## Maps

Integrated mapping for:

- APRS stations
- Aircraft
- Marine traffic
- Weather
- Receiver locations
- Propagation
- Signal reports

---

## Automation

Examples include:

- Record when a signal appears
- Alert when a callsign is detected
- Record satellite passes
- Trigger recordings from APRS messages
- Execute custom workflows
- Scheduled monitoring

---

## Alerting

Notifications through:

- Email
- Discord
- Matrix
- MQTT
- Webhooks
- SMS (future)

---

## Dashboard

Echo Base provides a modern browser-based operations center featuring:

- Receiver status
- Live waterfalls
- Spectrum displays
- Maps
- Signal history
- Decoder activity
- Messaging
- Recording controls
- Automation status
- System health

Designed to resemble a professional communications command center.

---

# Architecture

Echo Base follows a modular service-oriented architecture.

```text
                 Web Dashboard
                       │
               REST / WebSockets
                       │
               Echo Base API
                       │
      ┌────────────────┼────────────────┐
      │                │                │
 Receiver Manager  Radio Manager  Automation Engine
      │                │                │
      ├────────────────┼────────────────┤
      │                │                │
  SDR Drivers     Hamlib/CAT      Plugin System
      │                │                │
      └────────────────┼────────────────┘
                       │
              External Applications

     JS8Call
     Dire Wolf
     Pat
     WSJT-X
     FLDIGI
     dump1090
     rtl_433
     SatDump
     GNU Radio
````

---

# Plugin Architecture

Echo Base is designed to be extensible.

Plugins can provide:

* New SDR hardware
* Radio drivers
* Digital decoders
* Automation actions
* Dashboard widgets
* AI integrations
* Maps
* Recording engines

---

# Installation

Development installation:

```bash
git clone https://github.com/NoodleSploder/echo-base.git
cd echo-base
```

Installation tooling will be provided as the project matures.

Supported platforms:

* Ubuntu
* Debian
* Arch Linux
* Fedora (planned)
* Rocky Linux (planned)

---

# Project Status

Echo Base is currently in early development.

The initial milestone focuses on building the platform architecture, modular backend, web interface, receiver management, and plugin framework.

---

# Philosophy

Echo Base does not seek to replace excellent open-source radio software.

Instead, it provides a unified platform that coordinates, visualizes, automates, and extends those tools into a cohesive radio operations environment.

---

# Contributing

Contributions are welcome.

Areas of interest include:

* SDR hardware support
* Radio integrations
* Digital mode plugins
* UI/UX
* Mapping
* Recording
* Automation
* Documentation
* Testing

---

# License

Apache License 2.0

---

*"Every transmission tells a story. Echo Base helps you hear it."*

```
```
