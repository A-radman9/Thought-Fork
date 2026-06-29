# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
