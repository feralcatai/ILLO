# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI, etc.)
working in the ILLO repository.

> **Authoritative guide:** The full architecture, conventions, and development
> notes live in [`CLAUDE.md`](./CLAUDE.md). Read it first — this file is a quick
> orientation and a summary of the rules that matter most for automated changes.

## What this project is

ILLO is an AI-powered levitating UFO companion for the **Adafruit Circuit
Playground Bluefruit (nRF52840)**, written in **CircuitPython**. It is a
production embedded application, not a desktop Python app.

- **Entry point:** `code.py` (CircuitPython convention)
- **Filesystem remount:** `boot.py`
- **Runtime config:** `config.json`
- **Four routines:** UFO Intelligence, Intergalactic Cruising, Meditate, Dance Party

## Hard constraints (read before changing code)

1. **256KB RAM.** Memory is the dominant constraint. Prefer lazy imports, reuse
   objects, avoid temporary lists/dicts in tight loops, and rely on
   `MemoryManager.periodic_cleanup()`. See the "Memory Management Strategy"
   section in `CLAUDE.md`.
2. **CircuitPython, not CPython.** Target CircuitPython 10.2.1+. Many CPython
   stdlib modules and packages are unavailable. Only the Adafruit bundle libs
   and built-in modules (`time`, `os`, `gc`, `microcontroller`, …) exist on
   device.
3. **Single-threaded.** No threading; use non-blocking patterns in the main loop.
4. **New routines** inherit from `BaseRoutine` and implement `run(mode, volume)`.
   Wire them into `create_routine_instance()` in `code.py`.

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

See the "Project Structure Summary" in `CLAUDE.md` for the full map. Quick index:

| Area              | Files |
| ----------------- | ----- |
| Entry / config    | `code.py`, `boot.py`, `config.json`, `config_manager.py` |
| Routines          | `ufo_intelligence.py`, `intergalactic_cruising.py`, `meditate.py`, `dance_party.py` |
| Core managers     | `memory_manager.py`, `interaction_manager.py`, `light_manager.py` |
| UFO AI subsystems | `ufo_ai_core.py`, `ufo_ai_behaviors.py`, `ufo_learning.py`, `ufo_memory_manager.py`, `ufo_college_system.py`, `chant_detector.py` |
| Audio / BLE       | `audio_processor.py`, `music_player.py`, `bluetooth_controller.py`, `sync_manager.py` |
| Utilities         | `base_routine.py`, `hardware_manager.py`, `color_utils.py`, `college_manager.py` |
| Tests / tools     | `tests/`, `tools/` |
| Docs              | `docs/`, `apidocs/`, `README.md` |
