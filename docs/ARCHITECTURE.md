# Release Preflight architecture

Preflight is a local, deterministic, read-only release inspection tool.

## Non-negotiables

- Never modify the artifact being inspected.
- Core scanning requires no network access.
- Incomplete coverage must be visible.
- Findings must carry evidence and explain uncertainty.
- Expensive work such as hashing is selective and cacheable.
- Reports use relative paths to avoid leaking personal paths.

## Core pipeline

Artifact input → inventory → artifact facts / detection → rule engine → findings → comparison / history → UI, CLI, reports

These boundaries leave room for baselines, incremental rescans, release contracts,
archive inspection, Release Sets, CI, and cross-platform comparison without turning
the application into one giant module.
