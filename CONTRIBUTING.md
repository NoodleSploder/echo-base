# Contributing to Echo Base

First, thank you for your interest in contributing to Echo Base.

Echo Base is an ambitious open-source project whose goal is to become the definitive **Radio Operations Platform** for Linux. Rather than replacing existing radio software, Echo Base integrates and orchestrates the best tools in the amateur radio, SDR, communications, and RF ecosystems into a unified browser-based command center.

Whether you're fixing a typo, adding support for a new SDR, building a dashboard widget, improving documentation, or implementing a major subsystem, your contribution is appreciated.

---

# Project Philosophy

Echo Base follows several guiding principles:

- Build modular systems.
- Prefer plugins over hard-coded integrations.
- Keep APIs clean and well documented.
- Design for long-term maintainability.
- Integrate existing open-source projects rather than reinventing them.
- Make complex radio systems easy to configure and operate.
- Build software that is enjoyable to use.

The project values quality over quantity.

---

# Before You Begin

Please read the following documents before making architectural changes:

- `README.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `DEVELOPMENT_DIARY.md`

These documents describe:

- Project goals
- Architecture
- Current priorities
- Engineering decisions
- Future direction

---

# Development Workflow

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test your work.
5. Update documentation.
6. Submit a Pull Request.

Example:

```bash
git checkout -b feature/receiver-manager
```

---

# Coding Standards

## General

Write code that is:

- Readable
- Maintainable
- Modular
- Well documented
- Consistently formatted

Avoid large monolithic files.

Prefer smaller modules with clearly defined responsibilities.

---

## Python

Use:

- Type hints
- Dataclasses where appropriate
- Pydantic models
- Meaningful variable names
- Small functions
- Clear docstrings

Avoid:

- Global state
- Deep inheritance
- Circular imports

---

## Frontend

Use:

- React
- TypeScript
- Functional components
- Hooks
- Strong typing

Avoid:

- Large components
- Inline business logic
- Unnecessary state duplication

---

# Architecture

Echo Base is built around independent subsystems.

Examples include:

- Dashboard
- Receiver Manager
- Radio Manager
- Messaging
- Recording
- Maps
- Automation
- Plugin Manager

New functionality should integrate cleanly with existing modules.

Avoid introducing unnecessary coupling between subsystems.

---

# Plugins

Whenever practical, new hardware and software integrations should be implemented as plugins rather than modifications to the core platform.

Examples include:

- SDR hardware
- Radio drivers
- Digital decoders
- Dashboard widgets
- AI modules
- Automation actions

The long-term goal is for Echo Base to be extensible without requiring modifications to the core application.

---

# Documentation

Documentation is considered part of every contribution.

When adding significant functionality, update the appropriate documents:

| Document | Purpose |
|----------|---------|
| README.md | User-visible capabilities |
| ARCHITECTURE.md | Design decisions |
| ROADMAP.md | Project status |
| DEVELOPMENT_DIARY.md | Engineering history |

Documentation should remain synchronized with the codebase.

---

# Pull Requests

Pull requests should include:

- Purpose
- Summary of changes
- Screenshots (if UI changes)
- Testing performed
- Documentation updates

Small, focused pull requests are preferred over large multi-feature submissions.

---

# Reporting Issues

Bug reports should include:

- Operating system
- Hardware
- SDR model
- Radio model (if applicable)
- Echo Base version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs

Screenshots are always helpful.

---

# Feature Requests

Feature requests are encouraged.

Please describe:

- The problem
- Why it matters
- Your proposed solution
- Alternative approaches

Whenever possible, explain the operational use case.

---

# Supported Development Platforms

Primary development targets:

- Ubuntu LTS
- Debian
- Arch Linux

Future support:

- Fedora
- Rocky Linux
- Other Linux distributions

Windows and macOS are not primary development targets, although contributions improving compatibility are welcome.

---

# Areas Where Help Is Needed

Examples include:

## Backend

- FastAPI
- APIs
- WebSockets
- Database
- Authentication
- Scheduling

---

## Frontend

- React
- TypeScript
- Dashboard
- Data visualization
- Maps
- UI/UX

---

## SDR

- RTL-SDR
- Airspy
- SDRplay
- HackRF
- LimeSDR
- PlutoSDR

---

## Radio

- Hamlib
- CAT
- Vendor APIs
- Audio routing
- PTT

---

## Digital Communications

- APRS
- Winlink
- JS8
- Packet
- FT8
- SSTV
- DMR
- P25
- FreeDV

---

## Mapping

- Aircraft
- Marine
- APRS
- Satellite
- Propagation

---

## Recording

- Audio
- IQ
- Scheduling
- Playback

---

## Automation

- Rules engine
- Event processing
- Notifications
- Webhooks

---

## AI

Future contributors interested in artificial intelligence will eventually help build:

- Signal classification
- Occupancy analysis
- Decoder recommendations
- Recording summaries
- Natural language search
- RF analytics

---

# Project Goals

Echo Base aims to become:

- A unified radio operations platform
- A browser-based communications command center
- A modular automation framework
- A spectrum intelligence platform
- A foundation for future RF research and experimentation

This project is intentionally designed for long-term growth.

Architecture should always favor extensibility over short-term convenience.

---

# Code of Conduct

Be respectful.

Assume good intent.

Welcome new contributors.

Provide constructive feedback.

Remember that many contributors volunteer their time.

---

# License

By contributing to Echo Base, you agree that your contributions will be licensed under the Apache License 2.0.

---

# Thank You

Every contribution—whether code, documentation, testing, bug reports, or ideas—helps move Echo Base closer to becoming the premier open-source Radio Operations Platform.

We appreciate your time, expertise, and passion for radio.