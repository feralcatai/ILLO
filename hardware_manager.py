# Charles Doebler at Feral Cat AI
# Hardware management for Circuit Playground UFO

"""Hardware Abstraction Layer for Circuit Playground Bluefruit.

This module provides a simplified interface to Circuit Playground hardware,
abstracting NeoPixel control, audio output, and sensor access for UFO routines.

The hardware manager handles:
    - NeoPixel LED ring control and brightness management
    - Tone generation via piezo speaker
    - Hardware abstraction to simplify routine implementations
    - Battery-conscious default brightness settings

Classes:
    HardwareManager: Hardware abstraction for Circuit Playground

Example:
    >>> hardware = HardwareManager()
    >>> hardware.update_pixels_with_data(data, color_function)
    >>> hardware.play_tone_if_enabled(440, 0.2, volume=1)

Author:
    Charles Doebler at Feral Cat AI

Dependencies:
    - adafruit_circuitplayground
    - simpleio
"""

from adafruit_circuitplayground import cp
import simpleio
import time

class HardwareManager:
    def __init__(self):
        self.pixels = cp.pixels
        self.base_brightness = 0.1  # Default brightness for battery conservation
        self.pixels.brightness = self.base_brightness
        
    def update_pixels_with_data(self, pixel_data, color_func):
        """Update pixels based on data array and color function."""
        for ii in range(10):
            self.pixels[ii] = color_func(pixel_data[ii])
        self.pixels.show()
        
    def clear_pixels(self):
        """Clear all pixels."""
        self.pixels.fill(0)

    @staticmethod
    def play_tone_if_enabled(freq, duration, volume):
        """Play tone if volume is enabled."""
        if volume == 1:
            cp.play_tone(freq, duration, 1)

    @staticmethod
    def map_deltas_to_pixels(deltas):
        """Map audio deltas to pixel positions."""
        pixel_data = [0] * 10
        for ii, delta in enumerate(deltas):
            ix = round(simpleio.map_range(ii, 0, len(deltas), 0, 9))
            pixel_data[ix] += delta
        return pixel_data

    @staticmethod
    def get_accelerometer():
        """Get accelerometer data from the Circuit Playground."""
        return cp.acceleration

    @staticmethod
    def tap_detected():
        """Check if a tap has been detected."""
        return cp.tapped

    @staticmethod
    def shake_detected(threshold=11):
        """Check if a shake has been detected."""
        return cp.shake(shake_threshold=threshold)
    
    @property
    def light(self):
        """Get the current light sensor reading."""
        return cp.light
    
    @property
    def temperature(self):
        """Get the current temperature reading."""
        return cp.temperature
