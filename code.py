"""ILLO Main Controller - Multi-Routine UFO Lighting System.

This module serves as the main entry point for the ILLO project, managing routine
selection, configuration, and system resources across four distinct modes:

Routines:
    1. UFO Intelligence - AI-driven personality with learning behaviors
    2. Intergalactic Cruising - Smooth ambient lighting patterns
    3. Meditate - Breathing pattern visualization for meditation
    4. Dance Party - Synchronized multi-device light shows via BLE

Hardware Interface:
    - Button A: Cycle through routines (saves and reboots for clean switch)
    - Button B: Cycle through color/pattern modes (routine-specific)
    - Switch: Volume/sound enable flag (True=on, False=off)
    - NeoPixels: 10-pixel ring for visual effects
    - Sensors: Accelerometer (shake), microphone (audio), light sensor

Architecture:
    - TaskScheduler: Manages periodic operations (memory, config, status)
    - ConfigManager: Persistent configuration storage
    - MemoryManager: Tracks and optimizes memory usage
    - InteractionManager: Unified sensor input handling

Example:
    >>> # Normal operation (called automatically)
    >>> if __name__ == "__main__":
    ...     main()

Author:
    Charles Doebler at Feral Cat AI

Version:
    2.0.0 - Production Release

Dependencies:
    - adafruit_circuitplayground
    - config_manager, memory_manager, interaction_manager (local)
    - Routine-specific modules (lazy loaded)

Note:
    - Routine switching triggers automatic reboot for clean memory state
    - Debug flags control verbosity across subsystems
    - Volume parameter is boolean sound enable, not actual volume control
"""

# Charles Doebler at Feral Cat AI
#
# Button A cycles through routines (1-4)
# Button B cycles through color modes (1-4)
# Switch position controls volume (True/False)
# NeoPixel ring represents UFO lighting effects
# Microphone input creates reactive light patterns
# Accelerometer shake detection for "turbulence" effects

from adafruit_circuitplayground import cp
import time
from config_manager import ConfigManager
from memory_manager import MemoryManager
from interaction_manager import InteractionManager
import microcontroller
import os

# Version tracking
VERSION = "2.0.0"

# Debug Configuration - Set these flags to enable debug output
debug_bluetooth = False
debug_audio = False
debug_memory = False
debug_interactions = False


class TaskScheduler:
    """Simple task scheduler for managing periodic operations.

    Optimizes performance by controlling when different operations run.
    Tasks execute based on elapsed time intervals without blocking.

    Features:
        - Interval-based execution
        - Enable/disable tasks dynamically
        - Exception isolation (failed tasks don't crash the system)

    Example:
        ::

        scheduler = TaskScheduler()
        scheduler.add_task('cleanup', 30.0, gc.collect)
        scheduler.run_due_tasks(time.monotonic())
    """

    def __init__(self):
        """Initialize the task scheduler."""
        self.tasks = {}
        self.last_run = {}

    def add_task(self, name, interval, callback, enabled=True):
        """Add a scheduled task.

        Args:
            name (str): Task identifier
            interval (float): Seconds between executions
            callback (callable): Function to call
            enabled (bool): Whether a task is initially enabled
        """
        self.tasks[name] = {
            'interval': interval,
            'callback': callback,
            'enabled': enabled
        }
        self.last_run[name] = 0

    def enable_task(self, name):
        """Enable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = True

    def disable_task(self, name):
        """Disable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = False

    def run_due_tasks(self, current_time):
        """Run all tasks that are due to execute.

        Args:
            current_time (float): Current monotonic time

        Returns:
            list: Task names that were executed
        """
        executed_tasks = []

        for name, task in self.tasks.items():
            if not task['enabled']:
                continue

            if current_time - self.last_run[name] >= task['interval']:
                try:
                    task['callback']()
                    self.last_run[name] = current_time
                    executed_tasks.append(name)
                except MemoryError as mem_err:
                    print("[SCHEDULER] 🚨 Memory error in task %s: %s" % (name,
                                                                         str(mem_err)))
                    import gc
                    gc.collect()
                except Exception as e:
                    print("[SCHEDULER] ❌ Task %s failed: %s" % (name, str(e)))

        return executed_tasks


def _fs_writable_check():
    """Check if the CIRCUITPY filesystem is writable.

    Returns:
        bool: True if writable, False if USB is in read-only mode

    Note:
        Used to determine if persistent memory features can be enabled.
        Returns False on OSError (filesystem is read-only).
    """
    test_path = "._writetest.tmp"
    try:
        with open(test_path, "wb") as f:
            f.write(b"x")
        os.remove(test_path)
        return True
    except OSError:
        return False


def show_routine_feedback(routine):
    """Display visual feedback for routine selection.

    Args:
        routine (int): Routine number (1-4)

    Visual Pattern:
        Lights up N pixels for routine N with routine-specific color.
    """
    cp.pixels.fill((0, 0, 0))

    routine_info = {
        1: {"color": (100, 0, 255), "name": "UFO Intelligence"},
        2: {"color": (0, 255, 100), "name": "Intergalactic Cruising"},
        3: {"color": (0, 100, 255), "name": "Meditate"},
        4: {"color": (255, 100, 0), "name": "Dance Party"}
    }

    info = routine_info.get(routine, {"color": (255, 255, 255), "name": "Unknown"})

    for i in range(routine):
        cp.pixels[i] = info["color"]

    cp.pixels.show()
    print("🚀 Routine %d: %s" % (routine, info["name"]))


def show_mode_feedback(mode):
    """Display visual feedback for mode selection.

    Args:
        mode (int): Mode number (1-4)

    Visual Pattern:
        Uses quadrant positions (0, 3, 6, 9) with mode-specific colors.
    """
    cp.pixels.fill((0, 0, 0))

    mode_info = {
        1: {"color": (255, 0, 0), "name": "Rainbow Wheel"},
        2: {"color": (255, 0, 255), "name": "Pink Theme"},
        3: {"color": (0, 0, 255), "name": "Blue Theme"},
        4: {"color": (0, 255, 0), "name": "Green Theme"}
    }

    info = mode_info.get(mode, {"color": (255, 255, 255), "name": "Unknown"})

    positions = [0, 3, 6, 9]
    for i in range(mode):
        if i < len(positions):
            cp.pixels[positions[i]] = info["color"]

    cp.pixels.show()
    print("🎨 Mode %d: %s" % (mode, info["name"]))


def show_breathing_pattern_feedback(pattern):
    """Display visual feedback for breathing pattern selection.

    Args:
        pattern (int): Breathing pattern number (1-4)

    Visual Pattern:
        Expanding rings from the center, pattern N uses N rings.
        Includes smooth fade-out animation.
    """
    cp.pixels.fill((0, 0, 0))

    pattern_info = {
        1: {"color": (0, 150, 255), "name": "4-7-8 Breathing"},
        2: {"color": (100, 200, 100), "name": "Box Breathing"},
        3: {"color": (200, 100, 200), "name": "Triangle Breathing"},
        4: {"color": (255, 150, 0), "name": "Deep Relaxation"}
    }

    info = pattern_info.get(pattern, {"color": (255, 255, 255), "name": "Unknown"})

    # Center pixels (always lit)
    center_pixels = [4, 5]
    for pos in center_pixels:
        cp.pixels[pos] = info["color"]

    # Ring 1 (pattern 2+)
    if pattern >= 2:
        ring1_pixels = [3, 6]
        for pos in ring1_pixels:
            cp.pixels[pos] = tuple(int(c * 0.6) for c in info["color"])

    # Ring 2 (pattern 3+)
    if pattern >= 3:
        ring2_pixels = [2, 7]
        for pos in ring2_pixels:
            cp.pixels[pos] = tuple(int(c * 0.4) for c in info["color"])

    # Ring 3 (pattern 4 only - full ring)
    if pattern == 4:
        ring3_pixels = [1, 8, 0, 9]
        for pos in ring3_pixels:
            cp.pixels[pos] = tuple(int(c * 0.2) for c in info["color"])

    cp.pixels.show()
    print("🧘 Pattern %d: %s" % (pattern, info["name"]))
    time.sleep(1.2)

    # Smooth fade out
    for fade_step in range(10):
        for i in range(10):
            current_color = cp.pixels[i]
            if current_color != (0, 0, 0):
                faded_color = tuple(int(c * 0.8) for c in current_color)
                cp.pixels[i] = faded_color
        cp.pixels.show()
        time.sleep(0.1)

    cp.pixels.fill((0, 0, 0))
    cp.pixels.show()


def create_routine_instance(routine, config, bt_debug, audio_debug):
    """Create a routine instance based on a routine number.

    Uses lazy imports to save memory by only loading the necessary routines.

    Args:
        routine (int): Routine number (1-4)
        config (dict): Configuration dictionary
        bt_debug (bool): Bluetooth debug flag
        audio_debug (bool): Audio debug flag

    Returns:
        object or None: Routine instance if successful, None on failure

    Note:
        - Memory errors trigger immediate cleanup
        - UFO Intelligence validates AI subsystems after init
        - Returns None for invalid routine numbers
    """
    if not 1 <= routine <= 4:
        print("[SYSTEM] ❌ Invalid routine number: %d (must be 1-4)" % routine)
        return None

    instance = None

    # Extract config values
    name = config.get('name', 'ILLO')
    bluetooth_enabled = config.get('bluetooth_enabled', True)
    college_spirit_enabled = config.get('college_spirit_enabled', False)
    college = config.get('college', 'none')
    ufo_persistent_memory = config.get('ufo_persistent_memory', False)
    meditate_adaptive_timing = config.get('meditate_adaptive_timing', True)
    meditate_ultra_dim = config.get('meditate_ultra_dim', True)

    # Check filesystem for UFO Intelligence only
    _fs_is_writable = _fs_writable_check() if routine == 1 else False
    _persist_this_run = bool(ufo_persistent_memory and _fs_is_writable)

    try:
        if routine == 1:
            print("[SYSTEM] 🛸 Loading UFO Intelligence...")
            from ufo_intelligence import UFOIntelligence

            try:
                instance = UFOIntelligence(
                    device_name=name,
                    debug_bluetooth=bt_debug,
                    debug_audio=audio_debug,
                    persistent_memory=_persist_this_run,
                    college_spirit_enabled=college_spirit_enabled,
                    college=college
                )
            except MemoryError:
                print("[SYSTEM] 🚨 OUT OF MEMORY initializing UFO Intelligence")
                print(
                    "[SYSTEM] 💡 Try: 1) Restart, 2) Disable persistent memory, 3) Use simpler routine")
                return None

            # Validate AI subsystems
            if hasattr(instance, 'ai_core') and hasattr(instance,
                                                        'behaviors') and hasattr(
                instance, 'learning'):
                if instance.ai_core is None or instance.behaviors is None or instance.learning is None:
                    print("[SYSTEM] ❌ UFO Intelligence failed to initialize AI systems")
                    if hasattr(instance, 'cleanup'):
                        instance.cleanup()
                    return None

        elif routine == 2:
            print("[SYSTEM] 🌌 Loading Intergalactic Cruising...")
            from intergalactic_cruising import IntergalacticCruising
            instance = IntergalacticCruising()

            if bluetooth_enabled and hasattr(instance,
                                             'bluetooth') and instance.bluetooth:
                print("[SYSTEM] 📱 Enabling Bluetooth control...")
                instance.enable_bluetooth()
            else:
                print("[SYSTEM] ⚡ High-performance mode (Bluetooth disabled)")

        elif routine == 3:
            print("[SYSTEM] 🧘 Loading Meditate...")
            from meditate import Meditate
            instance = Meditate(
                adaptive_timing=meditate_adaptive_timing,
                ultra_dim=meditate_ultra_dim
            )

        elif routine == 4:
            print("[SYSTEM] 💃 Loading Dance Party...")
            from dance_party import DanceParty
            instance = DanceParty(name, bt_debug, audio_debug)

            if bluetooth_enabled and hasattr(instance, 'enable_bluetooth'):
                success = instance.enable_bluetooth()
                if not success and bt_debug:
                    print("[SYSTEM] ⚠️ Dance Party Bluetooth init issue")

            if bt_debug:
                print(
                    "[SYSTEM] 📡 Role determined by Button B (Mode 1=Leader, 2-4=Follower)")

        if instance:
            print("[SYSTEM] ✅ Routine %d loaded successfully" % routine)

        return instance

    except ImportError as import_err:
        print("[SYSTEM] ❌ Import error: %s" % str(import_err))
        print("[SYSTEM] 💡 Check that all required files are on CIRCUITPY")
        if instance and hasattr(instance, 'cleanup'):
            instance.cleanup()
        return None

    except MemoryError as mem_err:
        print("[SYSTEM] ❌ Memory error: %s" % str(mem_err))
        print("[SYSTEM] 💡 Try restarting or using a simpler routine")
        if instance and hasattr(instance, 'cleanup'):
            instance.cleanup()
        import gc
        gc.collect()
        return None

    except Exception as e:
        print("[SYSTEM] ❌ Unexpected error: %s" % str(e))
        if instance and hasattr(instance, 'cleanup'):
            instance.cleanup()
        return None


def handle_button_interactions(routine, mode, last_button_a_time, last_button_b_time,
                               button_debounce_delay, current_time):
    """Handle button A and B interactions with debouncing.

    Button A cycles routines and reboots. Button B cycles modes.

    Args:
        routine (int): Current routine (1-4)
        mode (int): Current mode (1-4)
        last_button_a_time (float): Last Button A press timestamp
        last_button_b_time (float): Last Button B press timestamp
        button_debounce_delay (float): Debounce delay in seconds
        current_time (float): Current monotonic time

    Returns:
        tuple: (new_routine, new_mode, new_last_button_a_time,
                new_last_button_b_time, config_changed)
    """
    config_changed = False

    # Button A: Routine selection (with reboot)
    if cp.button_a and (current_time - last_button_a_time > button_debounce_delay):
        routine = (routine % 4) + 1
        show_routine_feedback(routine)
        print("🔄 Switching to routine %d - saving and rebooting..." % routine)

        try:
            config_mgr = ConfigManager()
            config = config_mgr.load_config()
            config['routine'] = routine
            success = config_mgr.save_config(config)

            if success:
                print("💾 Routine %d saved successfully" % routine)
                time.sleep(1.5)
                cp.pixels.fill((0, 0, 0))
                cp.pixels.show()
                print("🚀 Rebooting...")
                time.sleep(0.5)

                if microcontroller:
                    microcontroller.reset()
                else:
                    print("❌ Cannot reboot (microcontroller module unavailable)")
                    config_changed = True
            else:
                print("❌ Failed to save, continuing without reboot")
                config_changed = True

        except Exception as e:
            print("❌ Error during save: %s" % str(e))
            config_changed = True

        last_button_a_time = current_time
        time.sleep(0.8)
        cp.pixels.fill((0, 0, 0))
        cp.pixels.show()

    # Button B: Mode selection
    if cp.button_b and (current_time - last_button_b_time > button_debounce_delay):
        mode = (mode % 4) + 1
        show_mode_feedback(mode)
        config_changed = True

        # Special feedback for Meditate
        if routine == 3:
            show_breathing_pattern_feedback(mode)
            breathing_patterns = {
                1: "4-7-8 Breathing",
                2: "Box Breathing",
                3: "Triangle Breathing",
                4: "Deep Relaxation"
            }
            print("[MEDITATE] 🧘 Mode %d = %s" % (mode, breathing_patterns.get(mode,
                                                                              "Unknown")))

        time.sleep(0.8)
        cp.pixels.fill((0, 0, 0))
        cp.pixels.show()
        last_button_b_time = current_time

    return routine, mode, last_button_a_time, last_button_b_time, config_changed


def handle_ufo_intelligence_learning(routine, current_routine_instance, interactions):
    """Handle UFO Intelligence learning from interactions.

    Only active for routine 1 (UFO Intelligence).

    Args:
        routine (int): Current routine number
        current_routine_instance (object): Active routine instance
        interactions (dict): Detected interactions from InteractionManager
    """
    if routine != 1 or not current_routine_instance:
        return

    # Update last interaction time
    if interactions['tap'] or interactions['shake']:
        if hasattr(current_routine_instance, 'last_interaction'):
            current_routine_instance.last_interaction = time.monotonic()
        if (hasattr(current_routine_instance, 'record_successful_attention') and
                getattr(current_routine_instance, 'mood', None) == "curious"):
            current_routine_instance.record_successful_attention()

    # Shake boosts energy
    if interactions['shake']:
        if hasattr(current_routine_instance, 'energy_level'):
            old_energy = current_routine_instance.energy_level
            current_routine_instance.energy_level = min(100,
                                                        current_routine_instance.energy_level + 15)
            if debug_interactions:
                print("[UFO AI] ⚡ Energy: %d -> %d" % (old_energy,
                                                       current_routine_instance.energy_level))

    # Light interactions
    if interactions.get('light_interaction', False):
        print("[UFO AI] 💡 Light interaction detected!")
        if hasattr(current_routine_instance, 'last_interaction'):
            current_routine_instance.last_interaction = time.monotonic()


def main():
    """Main application loop with task scheduling.

    Initializes system managers, loads configuration, and enters a main event loop.
    Handles routine switching, mode changes, and periodic maintenance tasks.
    """
    print("[SYSTEM] 🚀 ILLO v%s - Starting..." % VERSION)

    # Initialize managers
    config_mgr = ConfigManager()
    config = config_mgr.load_config()
    memory_mgr = MemoryManager(enable_debug=debug_memory)
    interaction_mgr = InteractionManager(enable_debug=debug_interactions)
    scheduler = TaskScheduler()

    # Load configuration
    routine = config.get('routine', 1)
    mode = config.get('mode', 1)
    ufo_persistent_memory = config.get('ufo_persistent_memory', False)

    # Check filesystem
    fs_is_writable = _fs_writable_check()
    persist_this_run = bool(ufo_persistent_memory and fs_is_writable)

    # State tracking
    current_routine_instance = None
    active_routine_number = 0
    last_button_a_time = 0.0
    last_button_b_time = 0.0
    button_debounce_delay = 0.3
    config_changed = False

    # Define scheduled tasks
    def memory_cleanup_task():
        """Periodic memory cleanup."""
        memory_mgr.periodic_cleanup()

    def config_save_task():
        """Save config if changes pending."""
        nonlocal config_changed, config, routine, mode
        if config_changed:
            config['routine'] = routine
            config['mode'] = mode
            success = config_mgr.save_config(config)
            if success:
                config_changed = False
                if debug_memory:
                    print("[SCHEDULER] 💾 Config auto-saved")

    def system_status_task():
        """Report system status."""
        import gc
        print("[SCHEDULER] 📊 Memory: %d bytes, Routine: %d, Mode: %d" %
              (gc.mem_free(), routine, mode))

    # Add tasks to a scheduler
    scheduler.add_task('memory_cleanup', 30.0, memory_cleanup_task)
    scheduler.add_task('config_save', 3.0, config_save_task)
    scheduler.add_task('system_status', 60.0, system_status_task, enabled=debug_memory)

    # Startup info
    actual_volume = cp.switch
    print("[SYSTEM] ✅ System initialized")
    print("[SYSTEM] 📊 Routine: %d, Mode: %d, Sound: %s" %
          (routine, mode, "ON" if actual_volume else "OFF"))

    if ufo_persistent_memory and not fs_is_writable:
        print("[SYSTEM] 💾 Persistent memory DISABLED (USB mounted)")
    elif persist_this_run:
        print("[SYSTEM] 💾 Persistent memory ENABLED")
    else:
        print("[SYSTEM] 💾 Persistent memory DISABLED")

    cp.detect_taps = 1

    # Performance tracking (debug only)
    loop_start_time = time.monotonic()
    loop_count = 0
    performance_report_interval = 100

    print("[SYSTEM] 🎮 Entering main loop...")

    # Main event loop
    while True:
        current_time = time.monotonic()
        volume = cp.switch
        loop_count += 1

        # Routine switching
        if routine != active_routine_number:
            print("[SYSTEM] 🔄 Switching routines...")

            # Clean up old routine
            if current_routine_instance:
                if hasattr(current_routine_instance, 'cleanup'):
                    try:
                        current_routine_instance.cleanup()
                    except Exception as cleanup_err:
                        print("[SYSTEM] ⚠️ Cleanup error: %s" % str(cleanup_err))

                memory_mgr.cleanup_before_routine_change()
                del current_routine_instance

                import gc
                gc.collect()
                print("[SYSTEM] 💾 Memory freed: %d bytes available" % gc.mem_free())

            # Set up a new routine
            interaction_mgr.setup_for_routine(routine)
            current_routine_instance = create_routine_instance(
                routine, config, debug_bluetooth, debug_audio
            )

            if current_routine_instance:
                active_routine_number = routine

                # Adjust memory cleanup interval
                if routine == 1:
                    scheduler.tasks['memory_cleanup']['interval'] = 20.0
                else:
                    scheduler.tasks['memory_cleanup']['interval'] = 30.0
            else:
                print("[SYSTEM] ❌ Failed to load routine %d" % routine)

        # Check interactions
        interactions = interaction_mgr.check_interactions(routine, volume, cp.pixels)
        handle_ufo_intelligence_learning(routine, current_routine_instance,
                                         interactions)

        # Handle buttons
        routine, mode, last_button_a_time, last_button_b_time, config_changed_by_button = \
            handle_button_interactions(
                routine, mode, last_button_a_time, last_button_b_time,
                button_debounce_delay, current_time
            )

        if config_changed_by_button:
            config['routine'] = routine
            config['mode'] = mode
            config_changed = True

        # Run active routine
        if current_routine_instance:
            try:
                current_routine_instance.run(mode, volume)
            except MemoryError as mem_err:
                print("[SYSTEM] 🚨 Memory error during routine: %s" % str(mem_err))
                import gc
                gc.collect()
                print("[SYSTEM] 💾 Emergency cleanup: %d bytes free" % gc.mem_free())
            except Exception as routine_err:
                print("[SYSTEM] ❌ Routine error: %s" % str(routine_err))

        # Run scheduled tasks
        scheduler.run_due_tasks(current_time)

        # Performance monitoring (debug)
        if debug_memory and loop_count % performance_report_interval == 0:
            elapsed = current_time - loop_start_time
            if elapsed > 0:
                loops_per_second = performance_report_interval / elapsed
                print("[SCHEDULER] 🚀 Performance: %.1f loops/sec" % loops_per_second)
            loop_start_time = current_time


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] ⏹️ Keyboard interrupt")
        cp.pixels.fill((0, 0, 0))
        cp.pixels.show()
        print("[SYSTEM] 👋 Goodbye!")
    except Exception as fatal_err:
        print("\n[SYSTEM] 💥 FATAL ERROR: %s" % str(fatal_err))
        # Flash red to indicate an error
        for _ in range(5):
            cp.pixels.fill((255, 0, 0))
            cp.pixels.show()
            time.sleep(0.2)
            cp.pixels.fill((0, 0, 0))
            cp.pixels.show()
            time.sleep(0.2)
