ILLO - AI-Powered Levitating UFO Companion
==========================================

Welcome to the ILLO API documentation! ILLO is an intelligent CircuitPython application
that brings levitating UFO platforms to life with adaptive artificial intelligence,
music-reactive visualizations, and college team spirit integration.

Overview
--------

ILLO transforms the Circuit Playground Bluefruit into an AI companion with four distinct
operating modes:

**UFO Intelligence** - An adaptive AI that learns from interactions and develops
personality traits over time. Features persistent memory, mood management, and
college spirit integration.

**Intergalactic Cruising** - Ambient sci-fi lighting with adaptive brightness,
audio reactivity, and optional Bluetooth control via the Bluefruit Connect app.

**Meditate** - Guided breathing patterns for meditation and relaxation, with four
different breathing techniques and adaptive timing based on ambient light.

**Dance Party** - Multi-device synchronized light shows using BLE for coordination,
with real-time beat detection and tempo matching.

Key Features
------------

* **Adaptive AI Learning** - Develops unique personality through interactions
* **Persistent Memory** - Remembers preferences across power cycles
* **College Spirit** - Customizable team colors, fight songs, and chant detection
* **Audio Processing** - Real-time FFT analysis for beat-synced visualizations
* **Environmental Sensing** - Adaptive brightness (2-25%) based on ambient light
* **Multi-Device Sync** - BLE-based synchronization for Dance Party mode
* **Memory Optimized** - Aggressive optimization for 256KB RAM constraint

Hardware Requirements
---------------------

* **Board**: Adafruit Circuit Playground Bluefruit (nRF52840)
* **Firmware**: CircuitPython 9.0.4+ (tested with 10.0.1)
* **RAM**: 256KB (requires careful memory management)
* **Storage**: 2MB flash for code and libraries
* **Features**: 10 NeoPixels, accelerometer, microphone, light sensor, BLE 5.0

Quick Start
-----------

1. Flash CircuitPython 9.0.4 or later to your Circuit Playground Bluefruit
2. Copy all ``.py`` files and the ``lib/`` directory to the CIRCUITPY drive
3. Copy ``config.json`` to configure your preferred mode and settings
4. Power on and enjoy! Button A cycles routines, Button B cycles modes

Configuration
-------------

Edit ``config.json`` to customize ILLO's behavior::

    {
      "name": "ILLO",
      "routine": 1,  // 1=AI, 2=Cruising, 3=Meditate, 4=Dance
      "mode": 1,     // Mode 1-4 (routine-specific)
      "bluetooth_enabled": true,
      "college": "penn_state",
      "college_spirit_enabled": false,
      "ufo_persistent_memory": true
    }

API Documentation
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Core System

   code
   config_manager
   memory_manager
   interaction_manager
   light_manager
   hardware_manager

.. toctree::
   :maxdepth: 2
   :caption: Operating Routines

   ufo_intelligence
   intergalactic_cruising
   meditate
   dance_party
   base_routine

.. toctree::
   :maxdepth: 2
   :caption: UFO AI Subsystems

   ufo_ai_core
   ufo_ai_behaviors
   ufo_learning
   ufo_memory_manager
   ufo_college_system

.. toctree::
   :maxdepth: 2
   :caption: Audio & College Integration

   audio_processor
   music_player
   chant_detector
   college_manager

.. toctree::
   :maxdepth: 2
   :caption: Bluetooth Systems

   bluetooth_controller
   sync_manager

.. toctree::
   :maxdepth: 2
   :caption: Utilities

   color_utils
   physical_actions

Architecture
------------

ILLO uses a modular architecture with lazy loading to manage the 256KB RAM constraint:

* **code.py** - Main entry point, routine orchestration, task scheduling
* **ConfigManager** - Persistent JSON configuration management
* **MemoryManager** - Garbage collection and memory monitoring
* **InteractionManager** - Unified sensor input handling
* **LightManager** - Adaptive brightness and interaction detection
* **BaseRoutine** - Abstract base class for all operating modes

Each routine inherits from ``BaseRoutine`` and implements the ``run(mode, volume)`` method.
The AI routine lazy-loads subsystems to minimize memory usage.

Memory Management
-----------------

ILLO implements aggressive memory optimization strategies:

* **Lazy imports** - Modules loaded only when needed
* **Periodic GC** - Automatic garbage collection every 10 seconds
* **Threshold monitoring** - Warnings at <5KB, critical at <2KB free
* **Cleanup on switch** - Routines cleaned before mode transitions
* **Flash protection** - Throttled save frequency for persistent memory

Development
-----------

See the ``CLAUDE.md`` file in the repository for detailed development guidance,
including common commands, architecture patterns, and best practices.

Support
-------

* **Repository**: https://github.com/feralcatai/ILLO
* **Issues**: https://github.com/feralcatai/ILLO/issues
* **Email**: charles@feralcatai.com
* **Website**: https://feralcatai.com

License
-------

MIT License - See LICENSE file for details.

Made with ❤️ in the USA by Feral Cat AI
