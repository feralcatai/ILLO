ILLO Bluetooth Control Guide
Intergalactic Cruising with Bluefruit Connect & Dance Party Multi-Device Sync

This guide covers two types of Bluetooth features in ILLO:
1. **Intergalactic Cruising**: Interactive control via Bluefruit Connect app
2. **Dance Party**: Automatic multi-device light show synchronization

================================================================================
DANCE PARTY MULTI-DEVICE SYNCHRONIZATION
================================================================================

Overview:

Dance Party mode features an advanced audio visualizer that can synchronize
multiple ILLO devices wirelessly. One device acts as the "leader" (analyzing
audio and broadcasting visual state), while other devices act as "followers"
(mirroring the leader's display).

Leader Mode (Mode 1):

- Analyzes audio frequency in real-time using FFT
- Creates rotating pixel patterns based on detected frequency
- Applies fade/persistence effects for smooth visual trails
- Broadcasts visual state via BLE advertisement names (12.5x per second)
- Shows idle comet animation when no audio is detected

Key Features:
- Frequency-reactive rotation speed (higher pitch = faster rotation)
- Dynamic color selection based on audio intensity
- Top 3 brightest pixels encoded for BLE transmission
- Automatic fallback to idle animation without audio

Follower Modes (Modes 2-4):

- Scans for leader BLE advertisements continuously
- Parses received visual state and renders locally
- Applies smoothing for natural-looking synchronization
- All follower modes behave identically (2, 3, 4 are equivalent)
- Automatic leader loss detection after 3 seconds

Key Features:
- Near real-time mirroring (~100ms latency typical)
- No audio processing required (fully silent operation)
- Automatic reconnection when leader returns
- Health tracking and diagnostic reporting

Protocol Details:

Advertisement Name Format:
ILLO_<seq>_<pos1>_<int1>_<col1>_<pos2>_<int2>_<col2>_<pos3>_<int3>_<col3>

Where:
- seq: Sequence number (0-255, wraps)
- pos: Pixel position (0-9)
- int: Intensity (0-255)
- col: Color type (0=red, 1=green, 2=blue/pink)

Example: "ILLO_42_5_180_1_4_120_1_3_80_2"
- Sequence 42
- Pixel 5: intensity 180, green
- Pixel 4: intensity 120, green  
- Pixel 3: intensity 80, blue/pink

Setup Instructions:

1. Configure Leader:
   - Switch to Dance Party mode (Button A to Routine 4)
   - Press Button B until Mode 1 (1 orange pixel blink)
   - Verify audio-reactive patterns appear when playing music

2. Configure Followers:
   - Switch to Dance Party mode on each follower device
   - Press Button B until Mode 2, 3, or 4 (any follower mode works)
   - Watch for follower to mirror leader's patterns

3. Verify Synchronization:
   - Play music near the leader device
   - All followers should mirror the rotating pattern
   - Typical latency: 80-150ms (nearly imperceptible)

Performance Tuning:

Three preset configurations available (requires code modification):

FAST MODE (Maximum Responsiveness):
- Broadcast rate: 50ms (20 times per second)
- Follower smoothing: 0.95 (near-instant)
- Best for: Tight sync, fast-paced music
- Trade-off: Higher battery drain

BALANCED MODE (DEFAULT):
- Broadcast rate: 80ms (12.5 times per second)
- Follower smoothing: 0.90 (snappy)
- Best for: General use, good balance
- Trade-off: Balanced performance and battery

SMOOTH MODE (Battery Saver):
- Broadcast rate: 120ms (8.3 times per second)
- Follower smoothing: 0.70 (fluid)
- Best for: Ambient displays, slower music
- Trade-off: Slightly more latency

To change presets, edit dance_party.py and uncomment desired configuration.

Troubleshooting Dance Party:

Followers Not Syncing:
- Verify bluetooth_enabled: true in config.json
- Ensure leader is in Mode 1, followers in Mode 2-4
- Check that devices are within 10-15 feet
- Restart all devices to reinitialize BLE radios

Laggy/Choppy Sync:
- Try FAST preset mode for better responsiveness
- Reduce distance between devices
- Ensure fresh batteries (low voltage affects BLE performance)
- Check for interference from other BLE devices

Leader Not Broadcasting:
- Verify leader shows audio visualization (confirms operation)
- Check bluetooth_enabled setting in config.json
- Ensure audio is reaching the microphone
- Try power cycling to reinitialize BLE

Partial Sync (some followers work, others don't):
- Position non-working followers closer to leader
- Check battery levels on all devices
- Verify config.json bluetooth setting on all devices
- Try setting non-working followers to different modes (2 vs 3 vs 4)

================================================================================
INTERGALACTIC CRUISING INTERACTIVE CONTROL
================================================================================

Congratulations on making your first Bluetooth connection! Your ILLO UFO now
supports wireless control through the Adafruit Bluefruit Connect app.

================================================================================
APP SETUP
================================================================================

Download Bluefruit Connect:

- iOS: App Store - Bluefruit Connect
- Android: Google Play - Bluefruit Connect

First Connection:

1. Switch to Intergalactic Cruising (Routine 2) using Button A on your Circuit
   Playground Bluefruit
2. Power on your ILLO UFO - it will automatically start advertising as
   "UFO" (or your configured device name)
3. Open Bluefruit Connect on your phone
4. Tap "Connect" and look for "UFO" in the device list
5. Connect within 2 minutes of powering on (advertising timeout)

TIP: Once paired, you can reconnect anytime even without active advertising!

================================================================================
CONTROL INTERFACES
================================================================================

1. Control Pad - Quick Actions

-------------------------------

The Control Pad provides instant access to color modes and effects:

**Numbered Buttons (1-4) - Color Modes:**
Button 1 | Rainbow Wheel | Full spectrum color cycling
Button 2 | Pink Nebula | Cosmic pink and magenta themes
Button 3 | Deep Space Blue | Rich blue cosmic variations
Button 4 | Forest Canopy | Natural green color palette

**Arrow Buttons - Settings:**
Up Arrow | Speed Boost | Increase rotation speed
Down Arrow | Speed Reduce | Decrease rotation speed  
Left Arrow | Gentle Mode | Softer effects and transitions
Right Arrow | Enhanced Mode | Intense effects and persistence

**Special Functions:**
Center | Manual Beat | Trigger instant beat sync for music
Reset Button | Audio Mode | Return to audio-reactive mode

2. Color Picker - Custom Colors

--------------------------------

Create your own color schemes:

- Tap the Color Picker in Bluefruit Connect
- Select any color from the wheel
- Your UFO instantly switches to that custom color
- Works with intensity: Brighter audio = brighter custom color

3. UART Terminal - Advanced Commands

-------------------------------------

For power users, type commands directly:

Basic Commands:
/help - Show all available commands
/status - Display current settings
/beat - Manual beat trigger

Color Mode Commands:
/mode 1 - Switch to Rainbow Wheel
/mode 2 - Switch to Pink Nebula
/mode 3 - Switch to Deep Space Blue
/mode 4 - Switch to Forest Canopy

Performance Tuning:
/speed 0.5 - Slow rotation (0.1x - 3.0x)
/speed 1.5 - Fast rotation
/brightness 50 - Set brightness to 50%
/brightness 100 - Maximum brightness

Example Session:
> /speed 2.0
> Rotation speed: 2.0x

> /brightness 75
> Brightness: 75%

> /mode 2
> Mode: Pink Nebula

> /status
> Current Settings:
> Mode Override: 4
> Speed: 2.0x
> Brightness: 75%
> Effect: normal

================================================================================
COLOR MODE DETAILS
================================================================================

1. Rainbow Wheel

- Full spectrum color cycling
- Smooth transitions through all hues
- Classic rainbow effect with dynamic intensity

2. Pink Nebula

- Cosmic pink and magenta themes
- Deep space nebula-inspired colors
- Rich purples, magentas, and hot pinks

3. Deep Space Blue

- Rich blue cosmic variations
- From light cyan to deep navy
- Evokes the depths of space

4. Forest Canopy

- Natural green color palette
- From bright lime to deep forest green
- Earth-inspired organic tones

================================================================================
MUSIC INTEGRATION
================================================================================

Audio Sync Methods:

1. Ambient Audio (Default):

- UFO uses its built-in microphone
- Play music from any source (phone speaker, stereo, etc.)
- UFO automatically reacts to ambient sound

2. Manual Beat Sync:

- Use Control Pad Center button or /beat command
- Perfect for syncing to silent music or creating your own rhythm
- Great for video recording with controlled lighting

3. Motion Sync (Future Feature):

- Accelerometer data could trigger beats
- Dance movements = light reactions

================================================================================
EFFECT MODES
================================================================================

Normal Mode (Default):

- Balanced intensity and fade
- Good for most music genres

Enhanced Mode (Right Arrow):

- More intense colors and effects
- Slower fade for persistence
- Perfect for electronic/dance music

Gentle Mode (Left Arrow):

- Softer colors and transitions
- Faster fade for subtle effects
- Great for ambient/classical music

================================================================================
PERSISTENT SETTINGS
================================================================================

Your color mode selections are automatically saved and will persist:

- Across power cycles
- When switching between routines
- Until manually changed

This means once you select "Pink Nebula", your UFO will remember and use
that color scheme even after restart!

Speed and effect settings are session-only and reset on restart.

================================================================================
CONNECTION MANAGEMENT
================================================================================

Connection Status:

- Green Status: Connected and receiving commands
- Advertising: Looking for connections (2 minutes)
- Standby: Can accept reconnections

Reconnection:

- Previously paired devices can reconnect anytime
- No need to wait for advertising
- Connection history stored in Bluefruit Connect

Troubleshooting:

- Can't connect? Wait for "Advertising..." message
- Lost connection? UFO will auto-restart advertising after 5 minutes
- Commands not working? Check UART Terminal for responses

================================================================================
CREATIVE USAGE IDEAS
================================================================================

Performance Mode:

1. Set custom colors with Color Picker
2. Use manual beat triggers for precise timing
3. Adjust speed and brightness for the scene

Party Mode:

1. Enhanced effects for maximum impact
2. High speed rotation (2.0x - 3.0x)
3. Let audio-reactive mode respond to music

Ambient Mode:

1. Gentle effects (Left arrow) for background ambiance
2. Deep Space Blue or Forest Canopy for calming colors
3. Speed reduction (Down arrow) for relaxed movement

Video Production:

1. Manual beat control for consistent lighting
2. Custom colors to match your aesthetic
3. Precise timing control via UART commands

================================================================================
QUICK REFERENCE CARD
================================================================================

**Color Modes:**

- Button 1: Rainbow Wheel
- Button 2: Pink Nebula
- Button 3: Deep Space Blue
- Button 4: Forest Canopy

**Speed Control:**

- Up Arrow: Faster rotation
- Down Arrow: Slower rotation

**Effects:**

- Right Arrow: Enhanced mode
- Left Arrow: Gentle mode
- Reset: Return to audio-reactive

**Special:**

- Center: Manual beat trigger
- Color Picker: Custom colors
- Terminal: /help for commands

Connection: Look for "UFO" in Bluefruit Connect
Timeout: 2 minutes initial, auto-readvertise every 5 minutes

================================================================================
WHAT'S NEXT?
================================================================================

Your ILLO UFO now supports advanced Bluetooth control! Try experimenting with:

- Different color modes with various music genres
- Speed adjustments for different energy levels
- Custom color combinations for specific moods
- Manual beat sync for creative video projects

The numbered buttons (1-4) give you instant access to the four signature
color themes, while the arrows let you fine-tune the experience. Your
selections are automatically saved, so your UFO remembers your preferences!

Enjoy your wirelessly controlled intergalactic cruising experience!

================================================================================
Technical Notes:

- Device Name: UFO (or your configured name from config.json)
- Bluetooth LE Protocol: Uses Adafruit Bluefruit Connect protocol
- Advertising Timeout: 2 minutes initial, 5 minute intervals for re-advertising
- Commands: Control Pad (!B), Color Picker (!C), UART Terminal (/)
- Persistent Storage: Color modes saved to config.json automatically
- Memory Optimized: Uses lazy imports to conserve CircuitPython memory
- Compatible: iOS and Android via Bluefruit Connect app
