# Echo Base Installation Guide

> **Version:** 0.1.0 (Draft)

This document describes how to install, configure, and run Echo Base.

Echo Base is designed as a Linux-first application and is intended to run as a long-lived service managing radios, SDRs, digital communications, automation, and spectrum intelligence.

---

# Supported Platforms

Primary development targets:

- Arch Linux
- Ubuntu 24.04 LTS
- Debian 12+
- Rocky Linux (planned)
- Fedora (planned)

Windows and macOS are not currently primary deployment targets.

---

# System Requirements

## Minimum

- Dual-core CPU
- 4 GB RAM
- 10 GB disk
- One RTL-SDR

---

## Recommended

- Quad-core CPU
- 16 GB RAM
- SSD storage
- USB 3.0
- Multiple SDR receivers

---

## Large Installations

- 8+ CPU cores
- 32 GB RAM
- NVMe storage
- Dedicated recording volume
- Multiple SDRs
- Network-attached receivers
- PostgreSQL

---

# Dependencies

Echo Base depends on:

## Backend

- Python 3.12+
- pip
- virtualenv

---

## Frontend

- Node.js 22+
- npm

---

## Database

Initially:

- SQLite

Future:

- PostgreSQL

---

## Optional Radio Software

Echo Base integrates with existing applications.

Examples:

- SoapySDR
- Hamlib
- rtl-sdr
- rtl_tcp
- dump1090
- readsb
- rtl_433
- Dire Wolf
- JS8Call
- Pat
- WSJT-X
- FLDIGI
- SatDump
- GNU Radio

None of these are strictly required to install Echo Base.

Features become available as supporting software is installed.

---

# Installation

## Clone Repository

```bash
git clone git@github.com:NoodleSploder/echo-base.git

cd echo-base
```

---

## Python Environment

```bash
python -m venv .venv

source .venv/bin/activate

pip install -U pip

# Runtime only:
pip install -r backend/requirements.txt

# Contributing / running tests (adds pytest, pytest-asyncio, httpx):
pip install -r backend/requirements-dev.txt
```

---

## Frontend

```bash
cd frontend

npm install

npm run build
```

---

## Backend

```bash
cd backend

uvicorn app.main:app --reload
```

---

## Development

Run backend:

```bash
cd backend

source ../.venv/bin/activate

uvicorn app.main:app --reload
```

Run frontend:

```bash
cd frontend

npm run dev
```

---

# Directory Layout

```
echo-base/

backend/

frontend/

plugins/

docs/

config/

data/

logs/

recordings/

scripts/

packaging/

tests/
```

---

# Configuration

Configuration lives in:

```
config/
```

Echo Base runs with zero configuration files -- everything has a
built-in default. To customize, copy the example and edit it:

```bash
cp config/config.example.yaml config/config.yaml
```

Any value can also be overridden with an `ECHO_BASE_*` environment
variable (nested via `__`), e.g. `ECHO_BASE_SERVER__PORT=9000`. Env
vars take precedence over `config.yaml`, which takes precedence over
built-in defaults. There is currently one file, not separate
`receivers.yaml`/`radios.yaml`/`users.yaml` -- users live in the
database and receivers are discovered live from plugins rather than
configured statically.

---

# Data Storage

Default directories:

```
data/

logs/

recordings/

cache/
```

Future installations may relocate these to:

```
/var/lib/echo-base

/var/log/echo-base
```

---

# Running

Development:

```bash
uvicorn app.main:app --reload
```

Production:

```bash
systemctl start echo-base
```

---

# systemd

Future releases will include:

```
echo-base.service

echo-base-worker.service

echo-base-scheduler.service
```

Typical commands:

```bash
sudo systemctl enable echo-base

sudo systemctl start echo-base

sudo systemctl status echo-base
```

---

# First Login

Default URL:

```
http://localhost:8088
```

There is no setup wizard yet. On the very first startup, if no user
accounts exist, Echo Base automatically creates an `admin` account with
a randomly generated password, printed once to the console/log with a
forced password change on first login. A future release will replace
this with an interactive wizard that also:

- Configures storage
- Discovers SDR hardware
- Configures plugins
- Verifies dependencies

---

# Hardware Detection

Currently implemented:

- RTL-SDR, via the `rtl_sdr` plugin (requires the `rtl-sdr` package's
  `rtl_test` tool on `PATH`)

Planned:

- SoapySDR devices
- Hamlib-compatible radios
- Audio interfaces
- Automatic hot-plug detection

---

# USB Permissions

Most SDR hardware requires udev rules.

Example:

```
packaging/udev/
```

Installation scripts will install the required rules automatically.

---

# Firewall

Typical ports:

| Service | Port |
|---------|------|
| HTTP | 8088 |
| HTTPS | 8443 |
| WebSocket | 8088 |

Additional ports may be required for:

- rigctld
- rtl_tcp
- MQTT
- External decoders

---

# Plugins

Installed plugins:

```
plugins/
```

Future versions:

```bash
echo plugins install rtl_sdr

echo plugins update

echo plugins remove
```

---

# Updating

Future installer:

```bash
echo update
```

Manual:

```bash
git pull

pip install -r backend/requirements.txt

npm install

npm run build
```

---

# Backup

Recommended backup locations:

```
config/

data/

recordings/

logs/

plugins/
```

SQLite database:

```
data/echo-base.db
```

---

# Troubleshooting

## Service Status

```bash
systemctl status echo-base
```

---

## Logs

```bash
journalctl -u echo-base
```

or

```
logs/
```

---

## Verify Python

```bash
python --version
```

---

## Verify Node

```bash
node --version

npm --version
```

---

## Verify SDR

```bash
rtl_test
```

---

## Verify Hamlib

```bash
rigctl --version
```

---

## Verify SoapySDR

```bash
SoapySDRUtil --find
```

---

# Docker (Future)

Future releases will include:

```
docker-compose.yml
```

Example:

```bash
docker compose up
```

---

# Installer Roadmap

Future versions will include:

## Interactive Installer

```bash
sudo ./install.sh
```

Capabilities:

- Install dependencies
- Configure users
- Install systemd services
- Configure udev rules
- Install plugins
- Detect SDR hardware
- Configure database
- Build frontend
- Create administrator account
- Launch setup wizard

---

## Package Managers

Planned support:

- AUR
- Debian packages
- RPM packages
- Docker images

---

# Uninstall

Future installer:

```bash
sudo ./uninstall.sh
```

Manual removal:

```bash
sudo systemctl stop echo-base

sudo rm -rf /opt/echo-base
```

Configuration and recordings may be preserved unless explicitly removed.

---

# Future Deployment Models

Echo Base is intended to support:

- Raspberry Pi
- Home radio station
- Portable field station
- Emergency Operations Center (EOC)
- Club station
- Contest station
- Search & Rescue
- Mobile command vehicle
- Enterprise radio monitoring
- Distributed receiver clusters
- Cloud-connected monitoring networks

---

# Philosophy

Installing Echo Base should be straightforward.

The long-term goal is that a new Linux system can become a fully functional radio operations platform with a single command:

```bash
curl -fsSL https://install.echo-base.org | sudo bash
```

The installer should handle dependency installation, service configuration, hardware discovery, plugin installation, and initial system setup automatically while remaining transparent and easily auditable.