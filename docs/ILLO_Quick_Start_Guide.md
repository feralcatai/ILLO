# ILLO Quick Start Guide — Kecksburg Festival Edition

**v2.0.3 | Single-routine festival build**

---

## What You Need

- **Adafruit Circuit Playground Bluefruit** (nRF52840)
- **CircuitPython 10.2.1** ([Download CPB UF2](https://circuitpython.org/board/circuitplayground_bluefruit/))
- **USB-micro B cable** for programming
- **USB-C cable** for power
- **Levitating UFO base** (compatible magnetic levitation platform)

---

## Installation

1. Flash CircuitPython 10.2.1 to the Circuit Playground Bluefruit
   - Double-tap reset to enter bootloader, drag UF2 to `CPLAYBOOT`
2. Copy all `.py` files to the root of `CIRCUITPY`
3. Copy the `music/` folder to `CIRCUITPY`
4. Copy the `lib/` folder to `CIRCUITPY`
5. Eject and disconnect USB

---

## Controls

| Control | Function |
|---|---|
| **Slide Switch LEFT** | Sound enabled |
| **Slide Switch RIGHT** | Sound disabled (longer battery) |

There are no button controls in the Kecksburg Festival Edition — ILLO runs autonomously.

---

## What ILLO Does

ILLO plays four UFO/sci-fi theme songs on a continuous loop with light shows and sensor reactivity.

### Song Rotation

| # | Song | Repeats | Pause Between |
|---|---|---|---|
| 1 | Close Encounters | 3× | 5s |
| 2 | X-Files Theme | 4× (A B A B) | 2s |
| 3 | Star Trek Fanfare | 1× | — |
| 4 | Also Sprach Zarathustra | 1× | — |

30 seconds of ambient animation plays between each song in the rotation.

### X-Files Alternating Riff

The X-Files theme alternates note 5 between E5 and G5 across its 4 repeats:
- Plays 1 & 3: E5
- Plays 2 & 4: G5

### Theremin Trigger

During the inter-song pause, sustained loud audio (≥1.5s above threshold) followed by silence fires the Theremin trigger — Close Encounters plays immediately as the next song regardless of rotation position.

### Shadow Detection

When someone leans over ILLO (sudden ambient light drop), a ripple animation runs around the pixel ring with an ascending chirp if sound is enabled.

### Mic Reactivity

Pixel brightness lifts with ambient crowd volume during both songs and pause animations.

---

## Serial Monitor Output

Connect via USB and open a serial terminal (115200 baud) to see status output:

```
[SYSTEM] ILLO v2.0.3 - Kecksburg Festival Edition
[SYSTEM] Loaded: Close Encounters
[MEM] 114000 bytes free
...
[MUSIC] Playing: X-Files Theme at 40 BPM
[MUSIC] Repeat 1/4 — pausing 2s
[MEM] 112000 bytes free
[LIGHT] Shadow detected — ripple!
[MIC] Sustained audio detected — arming trigger
[MIC] Trigger armed — waiting for silence
[MIC] Theremin trigger fired — queuing Close Encounters
```

**Memory health guide:**
- > 20KB free — normal operation
- < 20KB free — consider reducing song count
- < 5KB free — critical, likely to crash

---

## Tuning Constants

All field-adjustable thresholds are constants at the top of `code.py`:

| Constant | Default | Description |
|---|---|---|
| `PAUSE_BETWEEN_SONGS` | 30.0s | Ambient pause between songs |
| `CLOSE_ENCOUNTERS_REPEATS` | 3 | How many times the motif plays |
| `CLOSE_ENCOUNTERS_REPEAT_PAUSE` | 5.0s | Pause between CE repeats |
| `XFILES_REPEATS` | 4 | X-Files repeat count |
| `XFILES_REPEAT_PAUSE` | 2.0s | Pause between X-Files repeats |
| `MIC_AMBIENT_FLOOR` | 50 | Sound level below this = silence |
| `MIC_THEREMIN_THRESHOLD` | 200 | Level that counts as Theremin playing |
| `MIC_THEREMIN_DURATION` | 1.5s | Sustained audio needed to arm trigger |
| `MIC_SILENCE_DURATION` | 0.8s | Silence needed to fire trigger |
| `LIGHT_SHADOW_THRESHOLD` | 40 | Light drop that counts as a shadow |

---

## Adding or Editing Songs

Songs live in the `music/` directory as JSON files. All songs use BPM + sixteenth-note duration encoding:

```json
{
    "name": "My Song",
    "bpm": 120,
    "colors": {
        "primary": [R, G, B],
        "secondary": [R, G, B]
    },
    "notes": [
        [frequency_hz, duration_in_sixteenths],
        [0, 4]
    ]
}
```

- Frequency `0` = rest
- Duration is in sixteenth notes: 4 = quarter note, 8 = half note, 16 = whole note
- Songs with alternating variants use `notes_a` and `notes_b` instead of `notes`

To add a song to the rotation, add its path to `SONG_FILES` in `code.py`.

---

## Battery

- Expected runtime: ~5 hours with sound enabled, longer with sound off
- ILLO auto-adjusts pixel brightness to ambient light to conserve power
