# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-06-29

### Added
- React visual demo (`thought-fork-ui/`):
  - Dark theme with glassmorphism, color-coded fork panels, and streaming animations
  - PromptInput with configurable fork count (2–5 paths)
  - ForkPanel components with auto-scroll, blinking cursor, and stance badges
  - SynthesisPanel with copy-to-clipboard and session metadata
  - `useForkStream` hook for streaming via fetch + ReadableStream
  - Responsive layout (grid on desktop, stacked on mobile)
  - Runs at `localhost:5173`, connects to API at `localhost:8000`

## [0.2.0] - 2026-06-29

### Added
- Streaming FastAPI Layer:
  - `POST /fork` endpoint that streams interleaved SSE events from parallel forks, followed by synthesis.
  - `GET /forks/{session_id}` endpoint to retrieve past sessions.
  - `GET /health` endpoint for monitoring.
- SQLite persistence using `aiosqlite` to store completed sessions.
- Pydantic models for structured requests, responses, and SSE events.
- New dependencies: `fastapi`, `uvicorn`, `sse-starlette`, `aiosqlite`.

## [0.1.0] - 2026-06-29

### Added
- Concept definition document (CONCEPT.md) — defines Thought Fork, all vocabulary, and architecture
- Apache 2.0 License
- Contributors and authorship record
- This changelog
- Core fork engine:
  - `thought_fork/config.py` — ForkConfig and built-in stance definitions
  - `thought_fork/fork.py` — Fork dataclass and stance resolution
  - `thought_fork/manager.py` — ForkManager with parallel async fork execution
  - `thought_fork/synthesis.py` — SynthesisEngine with attributed convergence
- Basic terminal demo (`examples/basic_fork.py`)
