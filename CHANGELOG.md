# Changelog

All notable changes to the ILLO project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2026-05-31

### Added
- `AGENTS.md` — quick-orientation guide for AI coding agents
- CircuitPython 10.2.1 firmware binary added to `firmware/`
- **Kecksburg Festival Edition** — complete rewrite of `code.py` as a single-routine festival build
  - Plays four UFO/sci-fi theme songs in rotation: Close Encounters, X-Files, Star Trek Fanfare, Also Sprach Zarathustra
  - Mic-reactive brightness during both songs and inter-song pauses
  - Shadow detection: sudden ambient light drop triggers a ripple animation
  - Theremin trigger: sustained audio followed by silence immediately queues Close Encounters
  - Rotating scan animation during inter-song pauses
  - Serial memory reporting (`[MEM]`) after each song load and each playback cycle
- `music/` directory with song JSON files (BPM + sixteenth-note encoding)
  - `close_encounters.json` — five-note motif, plays 3× with 5s pauses
  - `xfiles.json` — main riff with alternating E5/G5 on note 5, plays 4× (A B A B)
  - `star_trek.json` — TOS fanfare, stacked fourths at BPM 60
  - `also_sprach.json` — opening motif

### Changed
- Updated target/tested CircuitPython firmware to 10.2.1 for the Circuit Playground Bluefruit
- Synced version to 3.0.0 across `CLAUDE.md`, `project.toml`, and `CHANGELOG.md`
- Removed `docs/build/` from git tracking (already gitignored)

## [2.0.1] - 2025-01-27

### Added
- Comprehensive module-level docstrings for API documentation
- CLAUDE.md file with detailed development guidance for Claude Code
- Improved Sphinx documentation with complete ILLO overview
- Better structured API documentation index

### Changed
- Updated all version strings to 2.0.1 for consistency
- Enhanced documentation configuration in docs/source/conf.py
- Improved docs/source/index.rst with complete project overview

### Fixed
- Version consistency across code.py and project.toml
- Documentation structure for better API reference generation

## [2.0.0] - 2024-11-26

### Added
- Dance Party routine with more responsive beat synchronization
- Enhanced audio-visualizer for UFO AI routine
- Centralized light management system with adaptive brightness (2-25% range)
- Light interaction detection (wave, shadow, movement)
- Comprehensive interaction manager for unified sensor handling
- College spirit integration with Penn State as default

### Changed
- Updated to CircuitPython 10.0.1 firmware
- Refactored light sensing and interaction detection into dedicated manager
- Improved memory management with periodic garbage collection
- Enhanced college integration architecture

### Fixed
- Mode save routine reliability
- Light interaction responsiveness
- Audio-visual synchronization timing

## [1.0.0] - 2024-09-01

### Added
- Initial production release
- Four operating modes:
  - UFO Intelligence: AI-powered adaptive companion with learning
  - Intergalactic Cruising: Ambient sci-fi lighting with audio reactivity
  - Meditate: Four breathing patterns for meditation
  - Dance Party: Multi-device BLE synchronized light shows
- Persistent AI memory system (ufo_memory.json)
- Personality development (curiosity, playfulness, calmness, loyalty)
- College system with fight song recognition and chant detection
- Real-time FFT audio analysis and beat detection
- Bluetooth 5.0 LE multi-device synchronization
- Adaptive environmental sensing and auto-brightness
- Configuration management via config.json
- Memory optimization for 256KB RAM constraint
- Task scheduler for periodic operations
- Hardware abstraction layer for Circuit Playground Bluefruit

### Hardware Support
- Target: Adafruit Circuit Playground Bluefruit (nRF52840)
- CircuitPython: 9.0.4+
- Features: 10 NeoPixels, accelerometer, microphone, light sensor, BLE

### Dependencies
- adafruit_ble
- adafruit_bluefruit_connect
- adafruit_circuitplayground
- adafruit_lis3dh.mpy
- adafruit_thermistor.mpy
- neopixel.mpy
- simpleio.mpy

## Format Notes

### Version Types
- **Major** (X.0.0): Breaking changes, major feature releases
- **Minor** (0.X.0): New features, enhancements, non-breaking changes
- **Patch** (0.0.X): Bug fixes, documentation updates, minor improvements

### Change Categories
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

**Project**: ILLO - AI-Powered Levitating UFO Companion
**Repository**: https://github.com/feralcatai/ILLO
**License**: MIT
**Made with ❤️ in the USA by Feral Cat AI**
