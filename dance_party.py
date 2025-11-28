"""Dance Party Routine - Multi-UFO Synchronized Light Show via BLE.

This module implements a synchronized dance party routine where multiple Circuit
Playground Bluefruit devices can synchronize their NeoPixel displays over Bluetooth
Low Energy (BLE) using advertisement names as the communication protocol.

The routine supports two roles:
    - **Leader**: Audio-reactive display with beat detection (Mode 1)
    - **Follower**: Mirrors leader's display in real-time (Modes 2-4)

Protocol Format:
    ILLO_<seq>_<pos1>_<int1>_<col1>_<pos2>_<int2>_<col2>_<pos3>_<int3>_<col3>

Example:
    >>> from dance_party import DanceParty
    >>> dance = DanceParty("ILLO_01", debug_bluetooth=True)
    >>> dance.run(mode=1, volume=1)  # Leader mode with audio (volume: 0=off, 1=on)

Author:
    Charles Doebler — Feral Cat AI

Dependencies:
    - adafruit_circuitplayground
    - adafruit_ble
    - audio_processor (optional)
    
Note:
    The "volume" parameter throughout this module is a sound enable flag (0=off, 1=on)
    rather than an actual volume control, since the Circuit Playground Bluefruit piezo
    speaker has no volume adjustment capability. The naming is maintained for consistency
    with the hardware switch and other routines.
"""

from base_routine import BaseRoutine
import time
import gc
from adafruit_circuitplayground import cp
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import Advertisement

# Optional project audio helper
try:
    from audio_processor import AudioProcessor

    _HAS_AUDIO = True
except Exception:
    _HAS_AUDIO = False


class DanceParty(BaseRoutine):
    """Leader/follower visual synchronization over BLE advertisement names.

    This class implements a synchronized light show routine where one device acts
    as a leader (audio-reactive) and others follow by mirroring the leader's display.

    The visual display consists of three pixels that form an animated baton:
        - Head pixel: Full intensity at current position
        - Trail1: 55% intensity, follows head by 1 step
        - Trail2/Spark: Temporary beat effect at 75% intensity

    Audio processing features (leader mode):
        - Two-stage smoothing prevents visual jitter
        - Hysteretic color switching prevents rapid flickering
        - Beat detection triggers direction changes and visual effects

    Attributes:
        device_name (str): BLE device identifier
        debug_bluetooth (bool): Enable verbose BLE debugging output
        debug_audio (bool): Enable verbose audio processing output
        sync_enabled (bool): Whether BLE sync is enabled via config
        sync_active (bool): Whether BLE is currently initialized and active
        ble (BLERadio): BLE radio instance (None if not initialized)

    Class Attributes:
        _NUM_PIXELS (int): Number of NeoPixels on the device (10)
        _BRIGHTNESS (float): Global brightness setting (0.0-1.0)
        _STEP_MS (int): Time between position updates in milliseconds
        _ADV_PERIOD_MS (int): BLE advertisement refresh rate in milliseconds
        _SCAN_BURST_S (float): Follower scan duration in seconds
        _LOSS_TIMEOUT_S (float): Follower timeout before declaring leader lost
        _MIN_RENDER_MS (int): Minimum time between render updates (rate limiting)
        _SMOOTH_ALPHA (float): Exponential smoothing factor for follower (0.0-1.0)


    Example:
        >>> # Leader mode with debugging
        >>> leader = DanceParty("LEADER_01", debug_bluetooth=True, debug_audio=True)
        >>> leader.run(mode=1, volume=1)  # volume: 0=off, 1=on

        >>> # Follower mode
        >>> follower = DanceParty("FOLLOWER_02")
        >>> follower.run(mode=2, volume=0)  # silent follower

    Note:
        - Mode 1 is always Leader
        - Modes 2-4 are always Follower (safe default for undefined modes)
        - Follower mode ignores audio input and mirrors leader visuals
        - Volume parameter is a sound on/off flag, not actual volume control
    """

    _NUM_PIXELS = 10
    _BRIGHTNESS = 0.20

    # ============================================================================
    # TUNING PARAMETERS - Adjust these two values to change responsiveness
    # ============================================================================

    # How often leader broadcasts updates (in milliseconds)
    # Lower = more responsive, but uses more CPU/battery
    # Range: 50-200ms | Recommended: 80ms (balanced) | Fast: 50ms | Smooth: 120ms
    # _ADV_PERIOD_MS = 80

    # How quickly follower responds to changes (0.0-1.0)
    # Higher = snappier/more responsive, but less smooth
    # Range: 0.5-0.95 | Recommended: 0.90 (snappy) | Fast: 0.95 | Smooth: 0.70
    # _SMOOTH_ALPHA = 0.90

    # ============================================================================
    # PRESET CONFIGURATIONS (uncomment one to use)
    # ============================================================================
    # FAST MODE: Maximum responsiveness, uses more resources
    # _ADV_PERIOD_MS = 50
    # _SMOOTH_ALPHA = 0.95

    # BALANCED MODE: Good responsiveness with reasonable resource usage (DEFAULT)
    _ADV_PERIOD_MS = 80
    _SMOOTH_ALPHA = 0.90

    # SMOOTH MODE: Slower but smoother, saves battery
    # _ADV_PERIOD_MS = 120
    # _SMOOTH_ALPHA = 0.70

    # ============================================================================
    # ADVANCED TIMING CONSTANTS (usually don't need to change these)
    # ============================================================================
    _STEP_MS = 260  # visual step timing (≈3.8 revs/min)
    _SCAN_BURST_S = 0.20  # follower scan burst duration
    _LOSS_TIMEOUT_S = 3.0  # follower loss detection timeout
    _MIN_RENDER_MS = 15  # ~66 FPS render rate limit

    def __init__(self, device_name, debug_bluetooth=False, debug_audio=False):
        """Initialize Dance Party routine.

        Args:
            device_name (str): BLE device identifier (e.g., "ILLO_01")
            debug_bluetooth (bool, optional): Enable BLE debugging output. Defaults to False.
            debug_audio (bool, optional): Enable audio debugging output. Defaults to False.

        Raises:
            ImportError: If required CircuitPython libraries are missing
            MemoryError: If insufficient memory for initialization

        Note:
            - Validates timing constants on initialization
            - Reports memory usage if debugging enabled
            - Attempts BLE initialization if enabled in config
        """
        super().__init__()
        self.device_name = device_name
        self.debug_bluetooth = bool(debug_bluetooth)
        self.debug_audio = bool(debug_audio)

        # Validate timing configuration
        if self._STEP_MS < 100 or self._STEP_MS > 1000:
            print("[DANCE] ⚠️ _STEP_MS out of recommended range (100-1000ms)")
        if self._ADV_PERIOD_MS > self._STEP_MS:
            print("[DANCE] ⚠️ _ADV_PERIOD_MS should be <= _STEP_MS for smooth sync")

        # Memory tracking
        if debug_bluetooth or debug_audio:
            self._initial_free_mem = gc.mem_free()
            print("[DANCE] 💾 Initial free memory: %d bytes" % self._initial_free_mem)

        # Config
        self.config = self._load_dance_config()
        self.sync_enabled = bool(self.config.get('bluetooth_enabled', True))

        # BLE
        self.ble = None
        self.sync_active = False
        self.sync_manager = None  # checked by code.py

        # Leader state
        self._seq = 0
        self._last_adv_ms = 0
        self._index = 0
        self._next_tick_ms = self._now_ms() + self._STEP_MS

        # Audio visualizer state (enhanced from Intergalactic Cruising)
        self.rotation_offset = 0.0
        self.last_update = time.monotonic()

        # Expressive motion state (leader)
        self._dir = 1  # +1 or -1
        self._gap = 1  # trail spacing (1 or 2)
        self._swing_ms = 0  # jitter applied to the next step after beats
        self._beat_on = False
        self._beat_timer = 0  # frames remaining for "pop"
        self._spark_pos = None  # transient spark position (uses third triple)

        # Follower state
        self._last_seen_t = None
        self._last_seq = None

        # Connection health tracking
        self._sync_success_count = 0
        self._sync_fail_count = 0
        self._last_health_report_t = 0

        # Role tracking
        self._role_announced = False
        self._current_role = None

        # Audio
        self._audio_ok = False
        if _HAS_AUDIO:
            try:
                self.audio = AudioProcessor()
                self._audio_ok = True
            except Exception as e:
                if self.debug_audio:
                    print("[DANCE] ⚠️ Audio init failed: %s" % e)

        # Smoothed energy, envelope and hysteretic color (leader)
        self._energy_lp = 120.0
        self._env = 120.0
        self._ctype = 2  # 0=red, 1=green, 2=blue/pink-ish

        # Pixels
        cp.pixels.auto_write = False
        cp.pixels.brightness = self._BRIGHTNESS
        self._clear_pixels()
        self._last_render_ms = 0
        self._smooth_rgb = [[0.0, 0.0, 0.0] for _ in range(self._NUM_PIXELS)]

        print("[DANCE] 🎵 Dance Party init — BLE=%s, audio=%s"
              % ("EN" if self.sync_enabled else "DIS",
                 "Y" if self._audio_ok else "N"))

        if self.sync_enabled:
            self._initialize_ble()
            if self.sync_active:
                self.sync_manager = self

        # Memory report after init
        if debug_bluetooth or debug_audio:
            final_free = gc.mem_free()
            used = self._initial_free_mem - final_free
            print(
                "[DANCE] 💾 Init used %d bytes, %d bytes remaining" % (used, final_free))

    def enable_bluetooth(self):
        """Enable Bluetooth if not already active.

        Returns:
            bool: True if BLE is active after call, False otherwise

        Note:
            This method is called by code.py to enable BLE dynamically.
            Safe to call multiple times - idempotent operation.
        """
        if self.sync_active:
            if self.debug_bluetooth:
                print("[DANCE] ✅ Bluetooth already active")
            return True
        try:
            self._initialize_ble()
            return self.sync_active
        except Exception as e:
            print("[DANCE] ❌ Bluetooth enable failed: %s" % e)
            return False

    def set_responsiveness(self, mode="balanced"):
        """Adjust synchronization responsiveness with preset modes.

        Args:
            mode (str): One of "fast", "balanced", or "smooth"
                - "fast": Maximum responsiveness (50ms ads, 0.95 alpha)
                - "balanced": Good balance (80ms ads, 0.90 alpha) [DEFAULT]
                - "smooth": Smoother motion (120ms ads, 0.70 alpha)

        Returns:
            bool: True if mode was applied successfully

        Example:
            >>> dance = DanceParty("ILLO_01")
            >>> dance.set_responsiveness("fast")  # Maximum responsiveness
            >>> dance.set_responsiveness("smooth")  # Battery-saving smooth mode
        """
        presets = {
            "fast": (50, 0.95),
            "balanced": (80, 0.90),
            "smooth": (120, 0.70)
        }

        if mode.lower() not in presets:
            print("[DANCE] ⚠️ Invalid mode '%s'. Use: fast, balanced, or smooth" % mode)
            return False

        adv_period, smooth_alpha = presets[mode.lower()]
        self._ADV_PERIOD_MS = adv_period
        self._SMOOTH_ALPHA = smooth_alpha

        print("[DANCE] 🎛️ Responsiveness set to '%s' (ads:%dms, alpha:%.2f)" % 
              (mode.upper(), adv_period, smooth_alpha))
        return True

    def set_custom_responsiveness(self, adv_period_ms, smooth_alpha):
        """Set custom responsiveness parameters.

        Args:
            adv_period_ms (int): Advertisement period in milliseconds (50-200)
            smooth_alpha (float): Smoothing factor 0.0-1.0 (higher = snappier)

        Returns:
            bool: True if parameters were valid and applied

        Example:
            >>> dance = DanceParty("ILLO_01")
            >>> dance.set_custom_responsiveness(60, 0.92)  # Custom tuning
        """
        if not (50 <= adv_period_ms <= 200):
            print("[DANCE] ⚠️ adv_period_ms must be 50-200ms")
            return False

        if not (0.5 <= smooth_alpha <= 0.95):
            print("[DANCE] ⚠️ smooth_alpha must be 0.5-0.95")
            return False

        self._ADV_PERIOD_MS = int(adv_period_ms)
        self._SMOOTH_ALPHA = float(smooth_alpha)

        print("[DANCE] 🎛️ Custom responsiveness (ads:%dms, alpha:%.2f)" % 
              (self._ADV_PERIOD_MS, self._SMOOTH_ALPHA))
        return True

    def run(self, mode, volume):

        """Main execution loop for Dance Party routine.

        Args:
            mode (int): Determines role. 1=Leader, 2-4=Follower (safe default)
            volume (int): Sound enable flag (0=off, 1=on). Note: Called "volume" for
                         consistency with hardware switch, but acts as boolean since
                         piezo speaker has no actual volume control. Passed to audio
                         processor for compatibility with other routines.

        Note:
            - Called repeatedly by main event loop in code.py
            - Leader mode: Draws audio-reactive visuals and broadcasts via BLE
            - Follower mode: Scans for leader and mirrors received visuals
            - Falls back to local audio visualization if BLE unavailable

        Example:
            >>> dance = DanceParty("ILLO_01")
            >>> while True:
            ...     dance.run(mode=1, volume=1)  # Leader with audio (sound enabled)
        """
        # Determine leader/follower based on mode
        is_leader = (mode == 1)

        # Announce role once when it's determined
        if not self._role_announced or self._current_role != is_leader:
            role_name = "LEADER" if is_leader else "FOLLOWER"
            sync_status = "enabled" if self.sync_active else "disabled"
            print("[DANCE] 💃 Role: %s (BLE sync %s)" % (role_name, sync_status))
            self._role_announced = True
            self._current_role = is_leader

        # Reinitialize BLE if mode changed and not yet active
        if self.sync_enabled and not self.sync_active:
            self._initialize_ble(is_leader)

        if not self.sync_active:
            # Local fallback: still show audio baton if possible
            self._leader_frame()
            self._advance_ring_if_due()
            return

        if is_leader:
            # Draw first, then handle BLE (keeps visuals smooth)
            self._leader_frame()
            self._advance_ring_if_due()
            self._leader_advertise_if_due()
        else:
            self._follower_loop()

        # Periodic GC under debug
        if self.debug_bluetooth and (self._seq % 50 == 0):
            gc.collect()

        time.sleep(0.001)

    def _leader_frame(self):
        """Render audio-reactive visualization with frequency-based rotation and persistence.

        This method implements an enhanced audio visualizer inspired by Intergalactic Cruising:
            - Frequency analysis from audio deltas
            - Rotating pixel patterns based on frequency
            - Fade/persistence effects for smooth trails
            - Idle comet animation when no audio detected

        The rendered state is cached in `_last_triples` for BLE broadcasting.

        Note:
            - Falls back to idle animation if audio unavailable
            - Frequency determines rotation speed
            - Top 3 brightest pixels encoded for BLE sync
        """
        if not self._audio_ok:
            self._idle_animation()
            return

        try:
            # Get audio samples and compute deltas
            samples = self.audio.record_samples()
            if not samples or len(samples) == 0:
                self._idle_animation()
                return

            deltas = self.audio.compute_deltas(samples)
            if not deltas:
                self._idle_animation()
                return

            # Calculate frequency from audio
            freq = self.audio.calculate_frequency(deltas)

            if freq is None:
                self._idle_animation()
                return

            if self.debug_audio and (self._seq % 50 == 0):
                print("[DANCE] 🎵 Freq: %.1f Hz" % freq)

            # Map deltas to pixel intensities
            pixel_data = [0] * self._NUM_PIXELS
            for i in range(min(len(deltas), self._NUM_PIXELS)):
                # Scale deltas to intensity range
                intensity = min(255, int(abs(deltas[i]) * 2.5))
                pixel_data[i] = intensity

            # Apply rotation based on frequency
            current_time = time.monotonic()
            time_delta = current_time - self.last_update
            rotation_increment = freq * time_delta * 0.01
            self.rotation_offset = (self.rotation_offset + rotation_increment) % self._NUM_PIXELS
            self.last_update = current_time

            # Clear and render with rotation
            self._clear_pixels()

            # Apply rotation and render pixels
            active_pixels = []
            for i in range(self._NUM_PIXELS):
                rotated_index = int((i + self.rotation_offset) % self._NUM_PIXELS)
                base_intensity = pixel_data[i]

                if base_intensity > 50:  # Threshold for visibility
                    # Dynamic color based on intensity (similar to hysteretic coloring)
                    if base_intensity > 200:
                        color_type = 0  # Red for high intensity
                    elif base_intensity > 140:
                        color_type = 1  # Green for medium
                    else:
                        color_type = 2  # Blue/pink for lower

                    rgb = self._themed_rgb(base_intensity, color_type)
                    cp.pixels[rotated_index] = rgb
                    active_pixels.append((rotated_index, base_intensity, color_type))

            cp.pixels.show()

            # Fade effect for persistence
            time.sleep(0.03)
            for i in range(self._NUM_PIXELS):
                current_color = cp.pixels[i]
                if current_color != (0, 0, 0):
                    faded_color = tuple(int(c * 0.75) for c in current_color)
                    cp.pixels[i] = faded_color

            # Cache top 3 brightest pixels for BLE sync
            active_pixels.sort(key=lambda x: x[1], reverse=True)
            self._last_triples = []
            for i in range(3):
                if i < len(active_pixels):
                    self._last_triples.append(active_pixels[i])
                else:
                    self._last_triples.append((0, 0, 2))

        except Exception as e:
            if self.debug_audio:
                print("[DANCE] 🎵 visualizer err: %s" % e)
            self._idle_animation()

    def _idle_animation(self):
        """Gentle rotating comet animation when no audio detected."""
        current_time = time.monotonic()

        if current_time - self.last_update > 0.15:
            self.rotation_offset = (self.rotation_offset + 1) % self._NUM_PIXELS

            self._clear_pixels()

            # Create rotating comet effect
            main_pos = int(self.rotation_offset)
            trail1_pos = (main_pos - 1) % self._NUM_PIXELS
            trail2_pos = (main_pos - 2) % self._NUM_PIXELS

            cp.pixels[main_pos] = self._themed_rgb(120, 2)
            cp.pixels[trail1_pos] = self._themed_rgb(80, 2)
            cp.pixels[trail2_pos] = self._themed_rgb(50, 2)

            cp.pixels.show()
            self.last_update = current_time

            # Cache for BLE sync
            self._last_triples = [
                (main_pos, 120, 2),
                (trail1_pos, 80, 2),
                (trail2_pos, 50, 2),
            ]

    def _themed_rgb(self, inten, ctype):
        """Convert intensity and color type to RGB tuple.

        Args:
            inten (int): Intensity value (0-255)
            ctype (int): Color type (0=red, 1=green, 2=blue/pink)

        Returns:
            tuple: RGB color tuple (r, g, b) with values 0-255
        """
        inten = int(inten)
        if inten <= 0:
            return (0, 0, 0)
        if ctype == 0:  # red-ish
            return (inten, int(inten * 0.15), int(inten * 0.15))
        elif ctype == 1:  # green-ish
            return (int(inten * 0.15), inten, int(inten * 0.15))
        else:  # blue/pink-ish
            return (int(inten * 0.3), int(inten * 0.05), inten)

    def _advance_ring_if_due(self):
        """Advance the ring position based on timing and swing effects.

        Updates the current position index if enough time has elapsed since
        the last position update. Applies swing timing offset from beat effects.

        Note:
            - Uses `_next_tick_ms` to avoid timing drift
            - Applies and then resets `_swing_ms` offset
        """
        t = self._now_ms()
        if t >= self._next_tick_ms:
            self._index = (self._index + self._dir) % self._NUM_PIXELS
            step = self._STEP_MS + (self._swing_ms if self._swing_ms else 0)
            self._next_tick_ms = t + step
            self._swing_ms = 0

    def _leader_advertise_if_due(self):
        """Advertise current visual state via BLE name if due.

        Builds advertisement name from cached visual state and broadcasts via BLE.
        Must stop and restart advertising to update the broadcast name.

        Raises:
            MemoryError: Triggers emergency GC and reports memory status

        Note:
            - Rate-limited by `_ADV_PERIOD_MS` (faster for visualizer sync)
            - MUST stop and restart advertising to broadcast new name
            - Errors are suppressed except MemoryError (always reported)
        """
        t = self._now_ms()
        if (t - self._last_adv_ms) < self._ADV_PERIOD_MS:
            return

        name = self._build_adv_name_from_triples()

        try:
            # Create fresh advertisement with new name
            adv = Advertisement()
            adv.complete_name = name

            # MUST stop advertising before starting with new name
            try:
                self.ble.stop_advertising()
            except Exception:
                pass  # May not be advertising yet

            # Start advertising with updated name
            self.ble.start_advertising(adv)

            # Success feedback
            if self.debug_bluetooth and (self._seq % 50 == 0):
                print("[DANCE] 📡 Broadcasting: %s" % name)

        except MemoryError as e:
            print("[DANCE] 🚨 MEMORY ERROR in advertising: %s" % e)
            gc.collect()
            print("[DANCE] 🧹 Emergency GC, freed to %d bytes" % gc.mem_free())
        except Exception as e:
            if self.debug_bluetooth and (self._seq % 20 == 0):
                print("[DANCE] ⚠️ ADV err: %s" % e)
        finally:
            self._last_adv_ms = t

    def _build_adv_name_from_triples(self):
        """Build BLE advertisement name from current visual state.

        Returns:
            str: Advertisement name in ILLO protocol format

        Format:
            ILLO_<seq>_<p1>_<i1>_<c1>_<p2>_<i2>_<c2>_<p3>_<i3>_<c3>

        Where:
            - seq: Sequence number (0-255, wraps)
            - p: Pixel position (0-9)
            - i: Intensity (0-255)
            - c: Color type (0=red, 1=green, 2=blue)

        Note:
            - Pads with zeros if fewer than 3 triples cached
            - Increments sequence number on each call
        """
        triples = getattr(self, "_last_triples", [])
        while len(triples) < 3:
            triples.append((0, 0, 0))
        self._seq = (self._seq + 1) % 256
        (p1, i1, c1) = triples[0]
        (p2, i2, c2) = triples[1]
        (p3, i3, c3) = triples[2]
        name = "ILLO_%d_%d_%d_%d_%d_%d_%d_%d_%d_%d" % (
            self._seq, p1, i1, c1, p2, i2, c2, p3, i3, c3
        )
        if self.debug_bluetooth and (self._seq % 20 == 0):
            print("[DANCE] 📡 ADV: %s" % name)
        return name

    def _follower_loop(self):
        """Follower mode: scan for leader advertisements and mirror visuals.

        Performs active BLE scan to find leader advertisements, parses received
        visual state, and renders to local NeoPixels with smoothing.

        Features:
            - Fast, short scan bursts for low latency
            - Immediate packet processing (no wait for scan completion)
            - Duplicate frame detection via sequence number
            - Connection health tracking (success/fail counts)
            - Leader loss detection with timeout
            - Periodic health reporting (every 30 seconds if debugging)

        Note:
            - Processes packets immediately for minimal latency
            - Shorter scan bursts allow more frequent updates
            - Clears display after `_LOSS_TIMEOUT_S` without leader packets
        """
        found = False
        packets_processed = 0

        # Active scan with reduced timeout for faster cycling
        for adv in self.ble.start_scan(
                Advertisement, timeout=self._SCAN_BURST_S, minimum_rssi=-90, active=True
        ):
            adv_name = ""
            try:
                if getattr(adv, "complete_name", None):
                    adv_name = adv.complete_name
                elif getattr(adv, "short_name", None):
                    adv_name = adv.short_name
            except Exception:
                adv_name = ""

            if not adv_name or not adv_name.startswith("ILLO_"):
                continue

            # Debug: show what we're receiving
            if self.debug_bluetooth and packets_processed == 0:
                print("[DANCE] 🔍 Received: %s" % adv_name)

            parsed = self._parse_name(adv_name)
            if not parsed:
                self._sync_fail_count += 1
                if self.debug_bluetooth:
                    print("[DANCE] ⚠️ Parse failed for: %s" % adv_name)
                continue

            found = True
            self._sync_success_count += 1
            self._last_seen_t = time.monotonic()
            packets_processed += 1

            # Render all new frames immediately (no sequence filtering)
            # This reduces latency at the cost of potential duplicate renders
            if self._last_seq is None or parsed["seq"] != self._last_seq:
                self._last_seq = parsed["seq"]
                self._render_triples(parsed["triples"])

                if self.debug_bluetooth and (self._last_seq % 20 == 0):
                    print("[DANCE] 🔗 Rendered seq=%d, triples=%s" % (self._last_seq, parsed["triples"]))

                # Exit immediately after rendering for minimal latency
                break

        self.ble.stop_scan()

        # Periodic health report (every 30 seconds)
        now = time.monotonic()
        if self.debug_bluetooth and (now - self._last_health_report_t) >= 30.0:
            total = self._sync_success_count + self._sync_fail_count
            if total > 0:
                success_rate = (self._sync_success_count * 100) // total
                lag_ms = int((now - (self._last_seen_t or now)) * 1000)
                print("[DANCE] 📊 Sync: %d%% success (%d/%d), lag: %dms" %
                      (success_rate, self._sync_success_count, total, lag_ms))
            self._last_health_report_t = now

        # Loss handling
        if not found and self._last_seen_t is not None:
            if (time.monotonic() - self._last_seen_t) >= self._LOSS_TIMEOUT_S:
                if self.debug_bluetooth:
                    print("[DANCE] ❌ leader lost — clearing")
                self._clear_pixels()
                self._last_seq = None

        # Minimal sleep to avoid busy-waiting but keep responsive
        time.sleep(0.001)

    def _parse_name(self, name):
        """Parse BLE advertisement name into visual state.

        Args:
            name (str): BLE advertisement name in ILLO protocol format

        Returns:
            dict or None: Dictionary with keys 'seq' (int) and 'triples' (list of tuples),
                or None if parsing failed or format invalid

        Format:
            ILLO_seq_p1_i1_c1_p2_i2_c2_p3_i3_c3

        Note:
            - Validates all values are within acceptable ranges
            - Replaces invalid triples with (0,0,0)
            - Returns None if name format is incorrect
        """
        try:
            parts = name.split("_")
            if len(parts) != 11:
                return None
            seq = int(parts[1])
            vals = [int(x) for x in parts[2:11]]
            triples = [(vals[0], vals[1], vals[2]),
                       (vals[3], vals[4], vals[5]),
                       (vals[6], vals[7], vals[8])]
            # Sanity clamp
            clean = []
            for (p, i, c) in triples:
                if 0 <= p < self._NUM_PIXELS and 0 <= i <= 255 and 0 <= c <= 2:
                    clean.append((p, i, c))
                else:
                    clean.append((0, 0, 0))
            return {"seq": seq, "triples": clean}
        except Exception:
            return None

    def _render_triples(self, triples):
        """Render received visual state to NeoPixels with minimal latency.

        Args:
            triples (list): List of (position, intensity, color_type) tuples

        Note:
            - Reduced rate limiting for faster updates (optimized for visualizer)
            - Higher smoothing alpha for snappier response with minimal lag
            - Maps color types to RGB: 0=red, 1=green, 2=blue/pink
            - Clamps all output values to valid NeoPixel range (0-255)
        """
        # Reduced rate-limit for faster render updates
        now = self._now_ms()
        if (now - self._last_render_ms) < self._MIN_RENDER_MS:
            return

        # Build target RGB for all 10 pixels from the 3 triples
        target = [[0, 0, 0] for _ in range(self._NUM_PIXELS)]
        for (pos, inten, ctype) in triples:
            pos = int(pos)
            inten = int(inten)
            ctype = int(ctype)

            if inten <= 0 or not (0 <= pos < self._NUM_PIXELS):
                continue

            # Map ILLO color types to RGB (optimized)
            if ctype == 0:  # red-ish
                r = inten
                g = int(inten * 0.15)
                b = int(inten * 0.15)
                if r == 0 and inten > 0:
                    r = 1
            elif ctype == 1:  # green-ish
                r = int(inten * 0.15)
                g = inten
                b = int(inten * 0.15)
            else:  # blue/pink-ish
                r = int(inten * 0.30)
                g = int(inten * 0.05)
                b = inten

            target[pos] = [r, g, b]

        # Faster exponential smoothing (higher alpha = less latency)
        a = self._SMOOTH_ALPHA
        for i in range(self._NUM_PIXELS):
            sr, sg, sb = self._smooth_rgb[i]
            tr, tg, tb = target[i]

            # Apply smoothing with optimized response
            sr = sr + (tr - sr) * a
            sg = sg + (tg - sg) * a
            sb = sb + (tb - sb) * a

            self._smooth_rgb[i] = [sr, sg, sb]

            # Fast cast + clamp for NeoPixel
            r = 0 if sr < 0 else (255 if sr > 255 else int(sr + 0.5))
            g = 0 if sg < 0 else (255 if sg > 255 else int(sg + 0.5))
            b = 0 if sb < 0 else (255 if sb > 255 else int(sb + 0.5))
            cp.pixels[i] = (r, g, b)

        cp.pixels.show()
        self._last_render_ms = now

    def _initialize_ble(self, is_leader=False):
        """Initialize BLE radio for leader or follower mode.

        Args:
            is_leader (bool, optional): True for leader mode, False for follower.
                Defaults to False.

        Note:
            - Leader mode seeds initial advertisement (may defer if error)
            - Sets `sync_active` flag on successful initialization
            - Safe to call multiple times (stops previous advertisement first)
        """
        try:
            self.ble = BLERadio()
            self.sync_active = True

            if is_leader:
                try:
                    name = "ILLO_0_0_0_0_0_0_0_0_0_0"
                    adv = Advertisement()
                    adv.complete_name = name
                    try:
                        self.ble.stop_advertising()
                    except Exception:
                        pass
                    self.ble.start_advertising(adv)
                except Exception as e:
                    if self.debug_bluetooth:
                        print("[DANCE] ⚠️ initial advertising deferred: %s" % e)

            if self.debug_bluetooth:
                print("[DANCE] ✅ BLE initialized")
        except Exception as e:
            print("[DANCE] ❌ BLE init failed: %s" % e)
            self.sync_active = False

    @staticmethod
    def _clear_pixels():
        """Clear all NeoPixels to black and update display."""
        cp.pixels.fill((0, 0, 0))
        cp.pixels.show()

    @staticmethod
    def _now_ms():
        """Get current monotonic time in milliseconds.

        Returns:
            int: Current time in milliseconds since boot
        """
        return int(time.monotonic() * 1000)

    def get_debug_status(self):
        """Return current status for debugging and monitoring.

        Returns:
            dict: Status dictionary with the following keys:
                - sync_active (bool): Whether BLE is initialized
                - seq (int): Current sequence number
                - free_memory (int): Available memory in bytes
                - sync_success (int): Successful sync count (follower)
                - sync_fail (int): Failed sync count (follower)
                - last_seen_age (float): Seconds since last leader packet (follower)

        Example:
            >>> dance = DanceParty("ILLO_01")
            >>> status = dance.get_debug_status()
            >>> print(status['free_memory'])
            45632
        """
        status = {
            'sync_active': self.sync_active,
            'seq': self._seq,
            'free_memory': gc.mem_free(),
            'sync_success': self._sync_success_count,
            'sync_fail': self._sync_fail_count
        }

        if self._last_seen_t:
            status['last_seen_age'] = time.monotonic() - self._last_seen_t

        return status

    @staticmethod
    def _load_dance_config():
        """Load configuration from ConfigManager or return defaults.

        Returns:
            dict: Configuration dictionary with at least 'bluetooth_enabled' key

        Note:
            Falls back to default config if ConfigManager unavailable
        """
        try:
            from config_manager import ConfigManager
            return ConfigManager().load_config()
        except Exception:
            return {'bluetooth_enabled': True}

    def cleanup(self):
        """Clean shutdown of Dance Party resources.

        Called by code.py when switching routines. Stops all BLE operations,
        clears NeoPixel display, and reports cleanup status if debugging.

        Note:
            - Safe to call multiple times
            - Catches and logs all exceptions during cleanup
            - Always attempts to clear pixels even if BLE cleanup fails
        """
        try:
            if self.ble:
                try:
                    self.ble.stop_advertising()
                except Exception:
                    pass
                try:
                    self.ble.stop_scan()
                except Exception:
                    pass

            self._clear_pixels()

            if self.debug_bluetooth:
                print("[DANCE] 🧹 Cleanup complete")

        except Exception as e:
            print("[DANCE] ⚠️ Cleanup error: %s" % e)