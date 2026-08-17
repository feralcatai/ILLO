"""ILLO Kecksburg Festival Controller.

Single-routine UFO companion designed for the Kecksburg UFO Festival.
Plays a rotating set of UFO/sci-fi theme songs with light shows,
and reacts to ambient sound and light via onboard sensors.

Mic reactivity:
    - During pauses: pixel brightness tracks crowd volume
    - During songs: base brightness lifts with volume
    - Theremin trigger: sustained audio followed by silence queues
      Close Encounters as the next song immediately

Light reactivity:
    - Shadow detection: sudden drop in ambient light triggers a ripple
      animation (someone leaning over ILLO)
    - Adaptive baseline normalizes to room lighting over time

Pixel animations:
    - During pauses: slow rotating scan around the ring with mic brightness

Hardware:
    - Adafruit Circuit Playground Bluefruit (nRF52840)
    - Switch: Sound enable (True=on, False=off)
    - NeoPixels: 10-pixel ring for visual effects

Author:
    Charles Doebler at Feral Cat AI

Version:
    2.0.3 - Production Release

Dependencies:
    - adafruit_circuitplayground
    - config_manager, memory_manager, interaction_manager (local)
    - Routine-specific modules (lazy loaded)

Note:
    - Routine switching triggers automatic reboot for clean memory state
    - Debug flags control verbosity across subsystems
    - Volume parameter is boolean sound enable, not actual volume control
"""

from adafruit_circuitplayground import cp
import time
import json
import gc

# Version tracking
VERSION = "2.0.3"

# Songs to play in rotation (loaded from music/ directory)
SONG_FILES = [
    "music/close_encounters.json",
    "music/xfiles.json",
    "music/star_trek.json",
    "music/also_sprach.json",
]

# Index of Close Encounters in SONG_FILES — queued on Theremin trigger
CLOSE_ENCOUNTERS_INDEX = 0

PAUSE_BETWEEN_SONGS = 30.0  # seconds between songs
CLOSE_ENCOUNTERS_REPEATS = 3  # how many times to play the motif back-to-back
CLOSE_ENCOUNTERS_REPEAT_PAUSE = 5.0  # seconds between repetitions

XFILES_INDEX = 1              # index of X-Files in SONG_FILES
XFILES_REPEATS = 4            # plays: A B A B (note 5 alternates E5/G5)
XFILES_REPEAT_PAUSE = 2.0     # seconds between repetitions

# Mic sensitivity tuning — adjust these in the field
MIC_AMBIENT_FLOOR = 50        # sound_level below this = silence
MIC_THEREMIN_THRESHOLD = 200  # sustained level that counts as Theremin playing
MIC_THEREMIN_DURATION = 1.5   # seconds of sustained audio to arm the trigger
MIC_SILENCE_DURATION = 0.8    # seconds of silence after audio to fire trigger

# Light sensor tuning — adjust if shadow detection is too sensitive/slow
LIGHT_SHADOW_THRESHOLD = 40   # drop in light level that counts as a shadow
LIGHT_BASELINE_RATE = 0.02    # how quickly baseline adapts to room changes (2%/reading)


# ---------------------------------------------------------------------------
# Light sensor state — simple inline baseline tracker (no class needed)
# ---------------------------------------------------------------------------
_light_baseline = None        # initialized on first reading
_light_last_check = 0.0       # monotonic time of last sample
_light_history = [0] * 5      # circular buffer
_light_history_idx = 0


def check_shadow():
    """Sample the light sensor and detect a sudden shadow.

    Maintains an adaptive baseline that drifts toward room ambient over time.
    Returns True once per shadow event (resets after detection).

    Returns:
        bool: True if a shadow was just detected.
    """
    global _light_baseline, _light_last_check, _light_history, _light_history_idx

    now = time.monotonic()
    if now - _light_last_check < 0.1:
        return False
    _light_last_check = now

    level = cp.light

    # Initialize baseline on first call
    if _light_baseline is None:
        _light_baseline = level
        return False

    # Store in circular buffer
    _light_history[_light_history_idx] = level
    _light_history_idx = (_light_history_idx + 1) % 5

    # Detect shadow: current level well below baseline
    drop = _light_baseline - level
    detected = drop > LIGHT_SHADOW_THRESHOLD

    # Adapt baseline slowly when no interaction
    if not detected:
        _light_baseline += (level - _light_baseline) * LIGHT_BASELINE_RATE

    return detected


def ripple_animation(color, sound_enabled):
    """Run a pixel ripple outward from pixel 0, twice around the ring.

    Used as the shadow-detection response. Plays a soft ascending tone
    if sound is enabled.

    Args:
        color (tuple): RGB base color for the ripple.
        sound_enabled (bool): Whether to play audio.
    """
    print("[LIGHT] Shadow detected — ripple!")

    # Two passes around the ring
    for _ in range(2):
        for i in range(10):
            cp.pixels.fill((0, 0, 0))
            # Bright leading pixel
            cp.pixels[i] = color
            # Dim trailing pixel
            cp.pixels[(i - 1) % 10] = tuple(max(0, int(c * 0.3)) for c in color)
            cp.pixels.show()
            if sound_enabled and _ == 0:
                # Soft ascending chirp on first pass only
                freq = 400 + i * 40
                cp.play_tone(freq, 0.04)
            else:
                time.sleep(0.05)

    cp.pixels.fill((0, 0, 0))
    cp.pixels.show()


def load_song(filepath):
    """Load a song JSON file from the filesystem.

    Args:
        filepath (str): Path to the song JSON file.

    Returns:
        dict or None: Song data, or None on failure.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print("[MUSIC] Failed to load %s: %s" % (filepath, str(e)))
        return None


def set_pixels(color, brightness=0.1):
    """Fill all NeoPixels with a color scaled by brightness.

    Args:
        color (tuple): RGB tuple.
        brightness (float): 0.0 to 1.0 scale factor.
    """
    r = int(color[0] * brightness)
    g = int(color[1] * brightness)
    b = int(color[2] * brightness)
    cp.pixels.fill((r, g, b))
    cp.pixels.show()


def pixels_off():
    """Turn off all NeoPixels."""
    cp.pixels.fill((0, 0, 0))
    cp.pixels.show()


def mic_brightness():
    """Sample the microphone and return a brightness boost.

    Maps cp.sound_level to a 0.0–0.12 brightness addition
    so louder sounds make the pixels glow brighter.

    Returns:
        float: Brightness boost value.
    """
    level = cp.sound_level
    if level < MIC_AMBIENT_FLOOR:
        return 0.0
    normalized = min(1.0, (level - MIC_AMBIENT_FLOOR) / (500 - MIC_AMBIENT_FLOOR))
    return normalized * 0.12


def play_song(song, sound_enabled, notes_key="notes"):
    """Play a song with synchronized light show and mic reactivity.

    Note brightness pulses on primary color. Rests use secondary color.
    Overall brightness lifts with ambient mic level.

    Args:
        song (dict): Song data loaded from JSON.
        sound_enabled (bool): Whether to play audio.
        notes_key (str): Which notes list to use ("notes", "notes_a", "notes_b").
    """
    notes = song.get(notes_key) or song.get("notes", [])
    bpm = song.get("bpm", 120)
    primary = tuple(song.get("colors", {}).get("primary", [0, 200, 100]))
    secondary = tuple(song.get("colors", {}).get("secondary", [0, 20, 40]))

    if not notes:
        return

    sixteenth = 30.0 / (bpm * 4)

    print("[MUSIC] Playing: %s at %d BPM" % (song.get("name", "?"), bpm))
    set_pixels(primary, 0.08)

    for note_data in notes:
        if not isinstance(note_data, list) or len(note_data) != 2:
            continue

        freq = int(note_data[0])
        duration_sixteenths = int(note_data[1])
        duration_seconds = duration_sixteenths * sixteenth

        boost = mic_brightness()

        if freq > 0:
            set_pixels(primary, 0.15 + boost)
            if sound_enabled:
                cp.play_tone(freq, duration_seconds)
            else:
                time.sleep(duration_seconds)
        else:
            set_pixels(secondary, 0.05 + boost)
            time.sleep(duration_seconds)

        # Short gap between notes
        time.sleep(sixteenth / 2)

    set_pixels(primary, 0.05)


def pause_with_ambient(seconds, color, theremin_state, sound_enabled):
    """Wait between songs with rotating scan animation and mic reactivity.

    A single brighter pixel sweeps around the ring while all others hold
    a dim base glow. Brightness tracks mic volume. Also monitors for
    shadow detection and the Theremin trigger pattern.

    Args:
        seconds (float): How long to pause.
        color (tuple): RGB base color.
        theremin_state (dict): Mutable Theremin trigger state.
        sound_enabled (bool): Whether to play audio (for ripple chirp).

    Returns:
        bool: True if Theremin trigger fired (play Close Encounters next).
    """
    end_time = time.monotonic() + seconds
    scan_pixel = 0
    scan_step_interval = 0.12   # seconds per pixel step — controls scan speed
    last_scan_step = time.monotonic()

    # Dim base color for ring fill
    base_r = max(1, int(color[0] * 0.03))
    base_g = max(1, int(color[1] * 0.03))
    base_b = max(1, int(color[2] * 0.03))
    base_color = (base_r, base_g, base_b)

    while time.monotonic() < end_time:
        now = time.monotonic()
        level = cp.sound_level
        boost = mic_brightness()

        # --- Shadow detection ---
        if check_shadow():
            ripple_animation(color, sound_enabled)
            # Reset scan position after ripple
            scan_pixel = 0
            last_scan_step = time.monotonic()

        # --- Rotating scan animation ---
        if now - last_scan_step >= scan_step_interval:
            scan_pixel = (scan_pixel + 1) % 10
            last_scan_step = now

            # Fill ring with dim base, boost with mic volume
            bright_base = (
                min(255, int(base_r + color[0] * boost)),
                min(255, int(base_g + color[1] * boost)),
                min(255, int(base_b + color[2] * boost)),
            )
            cp.pixels.fill(bright_base)

            # Bright leading pixel
            lead_brightness = 0.25 + boost
            cp.pixels[scan_pixel] = (
                min(255, int(color[0] * lead_brightness)),
                min(255, int(color[1] * lead_brightness)),
                min(255, int(color[2] * lead_brightness)),
            )
            # Medium trailing pixel
            trail = (scan_pixel - 1) % 10
            cp.pixels[trail] = (
                min(255, int(color[0] * (lead_brightness * 0.4))),
                min(255, int(color[1] * (lead_brightness * 0.4))),
                min(255, int(color[2] * (lead_brightness * 0.4))),
            )
            cp.pixels.show()

        # --- Theremin trigger state machine ---
        if level >= MIC_THEREMIN_THRESHOLD:
            if not theremin_state["armed"]:
                if theremin_state["armed_at"] == 0.0:
                    theremin_state["armed_at"] = now
                    print("[MIC] Sustained audio detected — arming trigger")
                elif now - theremin_state["armed_at"] >= MIC_THEREMIN_DURATION:
                    theremin_state["armed"] = True
                    print("[MIC] Trigger armed — waiting for silence")
            theremin_state["silence_start"] = 0.0

        elif level < MIC_AMBIENT_FLOOR:
            if theremin_state["armed"]:
                if theremin_state["silence_start"] == 0.0:
                    theremin_state["silence_start"] = now
                elif now - theremin_state["silence_start"] >= MIC_SILENCE_DURATION:
                    print("[MIC] Theremin trigger fired — queuing Close Encounters")
                    theremin_state["armed"] = False
                    theremin_state["armed_at"] = 0.0
                    theremin_state["silence_start"] = 0.0
                    return True
            else:
                theremin_state["armed_at"] = 0.0
                theremin_state["silence_start"] = 0.0

        time.sleep(0.05)

    return False


def main():
    """Main loop: load songs and play through them in rotation."""
    print("[SYSTEM] ILLO v%s - Kecksburg Festival Edition" % VERSION)
    print("[SYSTEM] Loading songs...")

    # Load all songs once at startup
    songs = []
    for filepath in SONG_FILES:
        song = load_song(filepath)
        if song:
            songs.append(song)
            print("[SYSTEM] Loaded: %s" % song.get("name", filepath))
        gc.collect()
        print("[MEM] %d bytes free" % gc.mem_free())

    if not songs:
        print("[SYSTEM] No songs loaded - check music/ directory")
        cp.pixels.fill((255, 0, 0))
        cp.pixels.show()
        return

    print("[SYSTEM] %d songs ready. Starting playback." % len(songs))
    print("[SYSTEM] Mic thresholds: theremin=%d, silence=%d" % (
        MIC_THEREMIN_THRESHOLD, MIC_AMBIENT_FLOOR))
    print("[SYSTEM] Shadow threshold: %d light units" % LIGHT_SHADOW_THRESHOLD)

    song_index = 0

    # Theremin trigger state — persists across pause calls
    theremin_state = {
        "armed": False,
        "armed_at": 0.0,
        "silence_start": 0.0,
    }

    while True:
        sound_enabled = cp.switch
        song = songs[song_index]
        primary = tuple(song.get("colors", {}).get("primary", [0, 200, 100]))

        # Songs with repeats play multiple times with short pauses between
        if song_index == CLOSE_ENCOUNTERS_INDEX:
            repeats = CLOSE_ENCOUNTERS_REPEATS
            repeat_pause = CLOSE_ENCOUNTERS_REPEAT_PAUSE
        elif song_index == XFILES_INDEX:
            repeats = XFILES_REPEATS
            repeat_pause = XFILES_REPEAT_PAUSE
        else:
            repeats = 1
            repeat_pause = 0.0

        for rep in range(repeats):
            if song_index == XFILES_INDEX:
                notes_key = "notes_a" if rep % 2 == 0 else "notes_b"
            else:
                notes_key = "notes"
            play_song(song, sound_enabled, notes_key)
            if rep < repeats - 1:
                print("[MUSIC] Repeat %d/%d — pausing %ds" % (rep + 1, repeats, int(repeat_pause)))
                pause_with_ambient(repeat_pause, primary, theremin_state, sound_enabled)

        next_index = (song_index + 1) % len(songs)

        # Pause — rotating scan, shadow detection, Theremin trigger
        triggered = pause_with_ambient(
            PAUSE_BETWEEN_SONGS, primary, theremin_state, sound_enabled
        )

        if triggered:
            song_index = CLOSE_ENCOUNTERS_INDEX
        else:
            song_index = next_index

        gc.collect()
        print("[MEM] %d bytes free" % gc.mem_free())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pixels_off()
        print("[SYSTEM] Stopped.")
    except Exception as e:
        print("[SYSTEM] FATAL: %s" % str(e))
        cp.pixels.fill((255, 0, 0))
        cp.pixels.show()
