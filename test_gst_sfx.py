#!/usr/bin/env python3
"""
Test script for GStreamer-based sound effects system.
Tests both default audio device and specific device targeting.
"""

import sys
import time
from pathlib import Path

# Add the quodlibet module to path
sys.path.insert(0, '/home/jwd/music_server/quodlibet')

from quodlibet.extapis.sfx import play_sfx, POWER_UP, POWER_DOWN

def test_default_device():
    """Test playing sound effects to default audio device"""
    print("=== Testing Default Audio Device ===")
    
    print(f"Playing POWER_UP sound: {POWER_UP}")
    play_sfx(POWER_UP)
    time.sleep(2)
    
    print(f"Playing POWER_DOWN sound: {POWER_DOWN}")
    play_sfx(POWER_DOWN)
    time.sleep(2)

def test_specific_device():
    """Test playing sound effects to specific audio devices"""
    print("\n=== Testing Specific Audio Devices ===")
    
    # Test with Intel ICH device (the main VirtualBox audio device)
    intel_sink = "pulsesink device=alsa_output.pci-0000_00_05.0.analog-stereo"
    print(f"Playing to Intel ICH device: {intel_sink}")
    play_sfx(POWER_UP, audio_sink=intel_sink)
    time.sleep(2)
    
    # Test with loopback device
    loopback_sink = "pulsesink device=alsa_output.platform-snd_aloop.0.analog-stereo"
    print(f"Playing to Loopback device: {loopback_sink}")
    play_sfx(POWER_DOWN, audio_sink=loopback_sink)
    time.sleep(2)

def test_invalid_device():
    """Test error handling with invalid audio device"""
    print("\n=== Testing Error Handling ===")
    
    # Test with non-existent device
    print("Testing invalid audio device (should fail gracefully)...")
    play_sfx(POWER_UP, audio_sink="pulsesink device=nonexistent_device")
    time.sleep(2)
    
    # Test with non-existent sound file
    print("Testing non-existent sound file (should fail gracefully)...")
    play_sfx("nonexistent_sound")
    time.sleep(1)

if __name__ == "__main__":
    print("GStreamer Sound Effects Test")
    print("============================")
    
    try:
        test_default_device()
        test_specific_device()
        test_invalid_device()
        
        print("\n=== Test Complete ===")
        print("All tests finished. Check for any error messages above.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()