# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI, etc.)
working in the ILLO repository.

> **Authoritative guide:** The full architecture, conventions, and development
> notes live in [`CLAUDE.md`](./CLAUDE.md). Read it first — this file is a quick
> orientation and a summary of the rules that matter most for automated changes.

## What this project is

ILLO is a levitating UFO companion for the **Adafruit Circuit Playground
Bluefruit (nRF52840)**, written in **CircuitPython**. It is a production
embedded application, not a desktop Python app.

**Current build: Kecksburg Festival Edition (v3.0.0)** — a single-routine
song player that rotates four UFO/sci-fi theme songs with mic reactivity,
shadow detection, and a theremin trigger for Close Encounters.

- **Entry point:** `code.py` — self-contained, no external routine modules
- **Filesystem remount:** `boot.py`
- **Songs:** `music/` directory, JSON files (BPM + sixteenth-note encoding)

## Hard constraints (read before changing code)

1. **256KB RAM.** Memory is the dominant constraint. Reuse objects, avoid
   temporary allocations in tight loops, and call `gc.collect()` between
   songs. Current headroom after loading all songs: ~114KB free.
2. **CircuitPython, not CPython.** Target CircuitPython 10.2.1+. Many CPython
   stdlib modules are unavailable. Only Adafruit bundle libs and built-ins
   (`time`, `gc`, `json`, …) exist on device.
3. **Single-threaded.** No threading; use non-blocking patterns in the main loop.
4. **No config.json in this build.** All tuning constants are at the top of
   `code.py` — `PAUSE_BETWEEN_SONGS`, `MIC_THEREMIN_THRESHOLD`, etc.

## Development workflow

```bash
# Run the test suite (host-side, uses mocks — see tests/mocks.py)
python tests/run_tests.py

# Deploy to a mounted CIRCUITPY drive
python tools/circuitpy_sync.py

# Monitor device serial output
python tools/serial_monitor.py

# Build API docs
cd docs && make html
```

`requirements.txt` lists **host/tooling** dependencies only (docs + dev tools).
On-device dependencies come from the Adafruit CircuitPython Bundle and are not
pip-installable.

## Conventions for agents

- **Match existing style** in the file you are editing (naming, comment density,
  print-based debug tags like `[SYSTEM]`).
- **Run `python tests/run_tests.py`** after changes that touch testable host
  logic (config, memory, audio managers).
- **Do not commit** `docs/build/`, `dist/`, `__pycache__/`, or `.venv/` — these
  are gitignored build artifacts.
- **Version is tracked in two places:** `VERSION` in `code.py` and `version` in
  `project.toml`. Update **both** when releasing, and reflect it in
  `CHANGELOG.md`.
- **Don't add heavyweight dependencies.** Anything that runs on-device must be
  available in CircuitPython.

## Where things live

| Area        | Files |
| ----------- | ----- |
| Entry point | `code.py` — entire festival build lives here |
| Boot        | `boot.py` — filesystem remount |
| Songs       | `music/close_encounters.json`, `music/xfiles.json`, `music/star_trek.json`, `music/also_sprach.json` |
| Firmware    | `firmware/` — CircuitPython 10.2.1 UF2 |
| Tools       | `tools/circuitpy_sync.py`, `tools/serial_monitor.py` |
| Docs        | `docs/ILLO_Quick_Start_Guide.md`, `CHANGELOG.md` |
