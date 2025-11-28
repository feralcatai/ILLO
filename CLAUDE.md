# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ILLO is an AI-powered levitating UFO companion designed for the Circuit Playground Bluefruit (nRF52840). It's a production-ready CircuitPython application with four distinct operating modes: UFO Intelligence (AI learning), Intergalactic Cruising (ambient lighting), Meditate (breathing patterns), and Dance Party (multi-device BLE sync).

**Target Hardware:** Adafruit Circuit Playground Bluefruit
**Platform:** CircuitPython 9.0.4+
**Memory Constraints:** 256KB RAM (requires aggressive optimization)
**Current Version:** 2.0.1

## Development Commands

### Testing on Hardware
```bash
# Deploy to device (requires CIRCUITPY drive mounted)
cp *.py /path/to/CIRCUITPY/
cp -r lib /path/to/CIRCUITPY/
cp config.json /path/to/CIRCUITPY/

# Monitor serial output (Windows)
python tools/serial_monitor.py

# Sync files to device (use the sync tool)
python tools/circuitpy_sync.py
```

### Code Documentation
```bash
# Build Sphinx documentation
cd docs
make html  # or: python -m sphinx -M html source build

# View API documentation (in browser)
cd docs/build/html
python -m http.server
```

### Configuration
All runtime configuration is stored in `config.json` at the root. Edit this file to change:
- Active routine (1-4)
- Active mode (1-4)
- College affiliation
- Bluetooth settings
- Persistent memory flags

## Architecture

### Entry Point & System Initialization

**`code.py`** is the main entry point (CircuitPython convention). It:
1. Loads configuration from `config.json` via `ConfigManager`
2. Initializes system managers (Memory, Interaction)
3. Creates the appropriate routine instance via lazy imports
4. Runs the main loop with scheduled tasks (TaskScheduler)
5. Handles button interactions (A=routine switch, B=mode switch)

**`boot.py`** remounts the filesystem as writable to enable persistent memory saves.

### Four Operating Modes (Routines)

Each routine inherits from `BaseRoutine` and implements a `run(mode, volume)` method:

1. **UFO Intelligence** (`ufo_intelligence.py`)
   - Complex AI system with learning and personality development
   - Composed of subsystems: AI Core, Behaviors, Learning, Memory Manager, College System
   - Uses lazy initialization to manage memory pressure
   - Supports persistent memory if filesystem is writable

2. **Intergalactic Cruising** (`intergalactic_cruising.py`)
   - Ambient sci-fi lighting with adaptive brightness
   - Optional Bluetooth control via Bluefruit Connect app (`bluetooth_controller.py`)
   - Rotation effects with audio reactivity

3. **Meditate** (`meditate.py`)
   - Four breathing patterns (4-7-8, Box, Triangle, Deep Relaxation)
   - Adaptive timing based on ambient light
   - Minimal interactions for distraction-free meditation

4. **Dance Party** (`dance_party.py`)
   - Multi-device BLE synchronization using advertisement names as protocol
   - Leader/follower architecture (Mode 1 = leader with audio, Modes 2-4 = followers)
   - Real-time FFT beat detection via `AudioProcessor`
   - Uses `SyncManager` for BLE coordination

### Core System Managers

**ConfigManager** (`config_manager.py`)
- Loads/saves JSON configuration
- Provides defaults if config is missing
- Used throughout all routines for persistent settings

**MemoryManager** (`memory_manager.py`)
- Periodic garbage collection (every 10s)
- Memory usage monitoring and warnings
- Critical memory threshold detection (< 2KB triggers alerts)
- Essential for 256KB RAM constraint

**InteractionManager** (`interaction_manager.py`)
- Centralized sensor input handling (tap, shake, buttons)
- Debouncing for all inputs
- Provides unified interface for routines to query user interactions

**LightManager** (`light_manager.py`)
- Adaptive brightness based on ambient light sensor (2%-25% range)
- Light interaction detection (wave detection, shadow detection)
- Maintains light history for spike detection
- Baseline adaptation over time

### UFO Intelligence Subsystems

The AI routine (`ufo_intelligence.py`) orchestrates several subsystems:

- **UFOAICore** (`ufo_ai_core.py`): Decision-making engine, mood management, attention-seeking behaviors
- **UFOAIBehaviors** (`ufo_ai_behaviors.py`): Specific behavioral patterns (celebrations, reactions, sleep)
- **UFOLearning** (`ufo_learning.py`): Learning algorithms and preference adaptation
- **UFOMemoryManager** (`ufo_memory_manager.py`): Persistent personality, experiences, relationships (JSON-based)
- **UFOCollegeSystem** (`ufo_college_system.py`): College spirit integration with fight songs and chants
- **ChantDetector** (`chant_detector.py`): Audio pattern matching for college chants

All subsystems are **lazy loaded** to minimize memory usage. The AI system validates initialization and gracefully degrades if subsystems fail to load.

### Audio Processing

**AudioProcessor** (`audio_processor.py`)
- Real-time FFT analysis via microphone
- Beat detection and BPM tracking
- Used by Dance Party (primary) and UFO Intelligence (reactive lighting)

**MusicPlayer** (`music_player.py`)
- Plays college fight songs via piezo speaker
- Integrates with college system

### Bluetooth Systems

**BluetoothController** (`bluetooth_controller.py`)
- Bluefruit Connect app integration (UART service)
- Used by Intergalactic Cruising for remote control
- Advertising timeout management and reconnection logic

**SyncManager** (`sync_manager.py`)
- Multi-device synchronization for Dance Party
- Advertisement-name-based protocol (no pairing required)
- Leader broadcasts state, followers mirror visuals
- Format: `ILLO_<seq>_<pixel_data>...`

### Utility Modules

**HardwareManager** (`hardware_manager.py`)
- Abstracts Circuit Playground hardware access
- Provides consistent interface for sensors, pixels, buttons

**ColorUtils** (`color_utils.py`)
- Color generation functions (wheel, pink, blue, green themes)
- HSV/RGB conversions and color manipulation

**PhysicalActions** (`physical_actions.py`)
- Legacy module for physical response patterns

## Memory Management Strategy

**Critical constraint:** 256KB RAM requires aggressive optimization.

### Best Practices
1. **Lazy imports**: Import routine modules only when needed (see `create_routine_instance()` in code.py)
2. **Periodic GC**: Use `MemoryManager.periodic_cleanup()` every 10s
3. **Explicit cleanup**: Call `cleanup()` on routine instances before switching
4. **Minimize allocations**: Reuse objects, avoid creating temporary lists/dicts in tight loops
5. **Monitor thresholds**: < 5KB = warning, < 2KB = critical

### Memory Errors
If memory errors occur during development:
- Run `gc.collect()` immediately
- Consider disabling persistent memory (`ufo_persistent_memory: false`)
- Simplify the active routine
- Check for leaked references in subsystems

## College Integration System

Colleges are defined as JSON files in `colleges/` directory (e.g., `penn_state.json`, `michigan.json`).

**Schema:**
```json
{
  "name": "Penn State",
  "colors": {
    "primary": [0, 60, 113],
    "secondary": [255, 255, 255]
  },
  "fight_song": "fight_song_data",
  "chants": ["WE ARE", "PENN STATE"]
}
```

The `CollegeManager` (`college_manager.py`) loads college data and integrates with AI behaviors.

## Configuration Reference

**config.json structure:**
```json
{
  "name": "ILLO",                          // Device name
  "routine": 1,                            // 1=AI, 2=Cruising, 3=Meditate, 4=Dance
  "mode": 1,                               // Mode 1-4 (routine-specific)
  "bluetooth_enabled": true,               // Enable BLE features
  "college": "penn_state",                 // College affiliation
  "college_spirit_enabled": false,         // Enable college behaviors
  "ufo_persistent_memory": true,           // Save AI learning (requires writable FS)
  "meditate_adaptive_timing": true,        // Adapt breathing to light levels
  "meditate_ultra_dim": true,              // Extra dim mode for meditation
  "college_chant_detection_enabled": false // Audio chant detection
}
```

## Hardware Interface

**Buttons:**
- Button A: Cycle routines (saves config and reboots for clean memory state)
- Button B: Cycle modes within current routine (no reboot)

**Switch:**
- Position controls audio enable (True=on, False=off)
- Not a volume control—Circuit Playground piezo has no volume adjustment

**Sensors:**
- 10 NeoPixel LED ring
- 3-axis accelerometer (shake detection)
- Microphone (FFT audio processing)
- Light sensor (adaptive brightness, 0-320 typical range)
- Temperature sensor (available but unused)

## Important Development Notes

### Filesystem Writes
- `boot.py` remounts filesystem as writable
- Check writability with `_fs_writable_check()` before saving
- Only UFO Intelligence uses persistent memory (AI learning data)
- USB connection may force read-only mode—disconnect USB for writes

### Routine Switching
- Button A switches routines and **triggers a reboot** (via `microcontroller.reset()`)
- This ensures clean memory state between routines
- Config is saved before reboot to persist the change

### Debug Flags
Set these flags in `code.py` to enable verbose output:
```python
debug_bluetooth = False
debug_audio = False
debug_memory = False
debug_interactions = False
```

### Version Management
- Version is tracked in `project.toml` and `code.py`
- Current: 2.0.1
- Update both locations when releasing

## Common Development Patterns

### Adding a New Routine
1. Create new module inheriting from `BaseRoutine`
2. Implement `run(mode, volume)` method
3. Add lazy import case in `create_routine_instance()` (code.py)
4. Update `show_routine_feedback()` with new routine color/name
5. Test memory usage thoroughly

### Adding a New College
1. Create JSON file in `colleges/` directory
2. Follow existing schema (colors, fight_song, chants)
3. Test with `college: "your_college"` in config.json
4. Chant detection requires audio patterns defined

### Modifying AI Behaviors
- Behaviors are in `ufo_ai_behaviors.py`
- Core decision logic is in `ufo_ai_core.py`
- Learning algorithms are in `ufo_learning.py`
- Persistent state is managed by `ufo_memory_manager.py`
- Always test with memory monitoring enabled

## Known Limitations

1. **Memory is extremely tight** - 256KB RAM shared with CircuitPython runtime
2. **No multithreading** - CircuitPython is single-threaded, use non-blocking patterns
3. **Bluetooth range** - BLE has ~10m range, affected by physical obstacles
4. **Audio quality** - Piezo speaker is low-fidelity, FFT is resource-intensive
5. **Battery life** - ~5 hours with adaptive brightness, less with audio processing
6. **Filesystem writes** - Limited flash wear, minimize save frequency

## Documentation Resources

- **Quick Start:** `docs/ILLO_Quick_Start_Guide.md`
- **Configuration:** `docs/ILLO_Device_Configuration_Guide.md`
- **Bluetooth Control:** `docs/ILLO_Bluetooth_Control_Guide.md`
- **API Docs:** `apidocs/` (Sphinx-generated)
- **README:** Full feature overview and marketing content

## Project Structure Summary

```
├── code.py                    # Main entry point
├── boot.py                    # Filesystem remount
├── config.json                # Runtime configuration
│
├── Routines (4 modes)
│   ├── ufo_intelligence.py    # AI companion
│   ├── intergalactic_cruising.py  # Ambient lighting
│   ├── meditate.py            # Breathing patterns
│   └── dance_party.py         # Multi-device sync
│
├── Core Managers
│   ├── config_manager.py      # JSON config handling
│   ├── memory_manager.py      # GC and monitoring
│   ├── interaction_manager.py # Sensor input
│   └── light_manager.py       # Adaptive brightness
│
├── UFO AI Subsystems
│   ├── ufo_ai_core.py         # Decision engine
│   ├── ufo_ai_behaviors.py    # Behavior patterns
│   ├── ufo_learning.py        # Learning algorithms
│   ├── ufo_memory_manager.py  # Persistent memory
│   ├── ufo_college_system.py  # College integration
│   └── chant_detector.py      # Audio pattern matching
│
├── Audio & BLE
│   ├── audio_processor.py     # FFT and beat detection
│   ├── music_player.py        # Fight song playback
│   ├── bluetooth_controller.py # Bluefruit Connect
│   └── sync_manager.py        # Multi-device BLE sync
│
├── Utilities
│   ├── base_routine.py        # Routine base class
│   ├── hardware_manager.py    # Hardware abstraction
│   ├── color_utils.py         # Color functions
│   └── college_manager.py     # College data loading
│
├── colleges/                  # College JSON definitions
├── lib/                       # CircuitPython libraries
├── docs/                      # User documentation
└── tools/                     # Development utilities
```
