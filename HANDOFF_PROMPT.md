# Echo Base Development Handoff

This document is consumed by AI coding agents (Claude Code, Codex, ChatGPT, Gemini, etc.) to ensure consistent development practices and project continuity.

The objective is to allow any agent to immediately understand the project philosophy, architecture, current status, and expected workflow before making changes.

---

# Before Writing Code

**Read these documents completely before making any modifications.**

In this order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `ROADMAP.md`
4. `DEVELOPMENT_DIARY.md`
5. `CONTRIBUTING.md`
6. `docs/PLUGIN_API.md`
7. `docs/REST_API.md`
8. `docs/INSTALL.md`

Do **not** begin implementing features until these documents have been reviewed.

They define the project's vision, architecture, conventions, and engineering direction.

---

# Project Overview

Echo Base is an open-source **Radio Operations Platform**.

It is **not** another SDR application.

Echo Base is intended to become the unified command-and-control platform for:

- Software Defined Radios
- Conventional transceivers
- Digital communications
- Messaging systems
- Recording
- Automation
- Spectrum intelligence
- Mapping
- Monitoring
- AI-assisted RF analysis

Think of Echo Base as the equivalent of a:

- Network Operations Center (NOC)
- Security Operations Center (SOC)
- Mission Control
- Communications Command Center

for radio systems.

---

# Philosophy

Echo Base does **not** replace existing radio software.

Instead, it orchestrates best-in-class open-source projects.

Examples include:

- SoapySDR
- rtl-sdr
- Hamlib
- dump1090
- readsb
- rtl_433
- Dire Wolf
- Pat
- JS8Call
- WSJT-X
- FLDIGI
- SatDump
- GNU Radio

Echo Base becomes the control plane.

---

# Engineering Principles

Always favor:

- Modular design
- API-first development
- Loose coupling
- Plugin architecture
- Service-oriented design
- Strong typing
- Clean documentation
- Long-term maintainability

Avoid:

- Monolithic files
- Tight coupling
- Hidden dependencies
- Hard-coded hardware support
- Feature-specific hacks

---

# Architecture

Echo Base consists of loosely coupled services communicating through:

- REST APIs
- WebSockets
- Internal Event Bus

Subsystems should evolve independently.

Examples:

- Dashboard
- Receiver Manager
- Radio Manager
- Plugin Manager
- Recording Engine
- Messaging
- Automation
- Scheduler
- Spectrum Intelligence
- Maps
- AI

Do not tightly couple these systems.

---

# Plugin Philosophy

Whenever practical:

Implement new functionality as plugins.

Examples:

- SDR hardware
- Radios
- Decoders
- Dashboard widgets
- AI modules
- Automation actions

Do not modify the platform core unless necessary.

---

# Technology Stack

Backend

- Python
- FastAPI
- asyncio
- SQLAlchemy
- SQLite initially

Frontend

- React
- TypeScript
- Tailwind CSS
- Vite

Deployment

- Linux
- systemd
- Native installation

---

# Documentation Requirements

Documentation is considered part of every implementation.

Whenever meaningful work is completed:

## README.md

Update when user-visible capabilities change.

---

## ARCHITECTURE.md

Update when architectural decisions change.

---

## ROADMAP.md

Update project status.

Move work between:

- Completed
- In Progress
- Remaining

Do **not** turn ROADMAP into a changelog.

---

## DEVELOPMENT_DIARY.md

Append a new entry.

Every development session should record:

- Date
- Summary
- Motivation
- Features added
- Bugs fixed
- Architecture decisions
- Files modified
- Verification
- Outstanding work
- Recommended next steps

Do **not** overwrite previous entries.

Always append.

---

# Coding Standards

Write code that is:

- Modular
- Well documented
- Type annotated
- Readable
- Testable

Small files are preferred over very large modules.

Favor composition over inheritance.

---

# API Standards

Everything should be accessible through:

- REST APIs
- WebSockets

The frontend should consume the same public APIs available to external clients.

Avoid creating private backend interfaces exclusively for the frontend.

---

# Current Development Strategy

Unless otherwise directed, continue development in this order:

1. Project scaffolding
2. Backend framework
3. Frontend framework
4. Configuration system
5. Logging
6. Authentication
7. Plugin framework
8. Receiver Manager
9. Dashboard
10. Radio Manager
11. Recording
12. Messaging
13. Automation
14. Maps
15. AI

If implementation priorities change, update the ROADMAP.

---

# Before Committing

Verify:

- Project builds successfully.
- Documentation is synchronized.
- ROADMAP reflects current status.
- DEVELOPMENT_DIARY has been updated.
- No unnecessary files were added.
- Formatting is consistent.

---

# Commit Messages

Use concise, descriptive commit messages.

Examples:

```
Add receiver management framework

Implement FastAPI application scaffold

Create plugin discovery system

Add receiver REST endpoints

Implement WebSocket event bus

Create dashboard layout

Add SDR discovery service
```

Avoid generic commit messages like:

```
Fix stuff

Updates

Changes

Misc
```

---

# Long-Term Vision

Echo Base is expected to evolve into a comprehensive radio operations platform capable of supporting:

- Amateur radio
- SDR monitoring
- Aviation
- Marine
- Weather
- Satellite operations
- Search & Rescue
- Emergency communications
- Public safety monitoring
- Research
- Education
- RF experimentation
- Spectrum intelligence
- Distributed receiver networks
- AI-assisted signal analysis

Architecture decisions should always support this long-term vision.

---

# When Unsure

If multiple implementation approaches are possible:

Choose the solution that is:

- More modular
- More extensible
- Better documented
- Easier to maintain
- More reusable
- Less tightly coupled

Optimize for the platform Echo Base will become in five years, not merely the feature being implemented today.

---

# Final Instruction

Treat Echo Base as a long-term open-source platform rather than a collection of utilities.

Every architectural decision should improve:

- Extensibility
- Maintainability
- Observability
- Reliability
- User experience
- Developer experience

The objective is to build the definitive open-source Radio Operations Platform.

Always leave the project in a better state than you found it.