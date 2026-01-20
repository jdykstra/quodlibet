#!/usr/bin/env python3
"""
Test script for the sfx.py module to verify sound playback works.
"""

import sys
import os
sys.path.insert(0, '/home/jwd/music_server/quodlibet')

from quodlibet.extapis.sfx import play_sfx, POWER_UP
from gi.repository import GLib
import time

def test_sfx():
    print("Testing SFX playback...")
    
    # Test with one of the predefined sound names
    play_sfx(POWER_UP)
    
    # Give the main loop a chance to process
    main_loop = GLib.MainLoop()
    
    def quit_after_delay():
        print("Stopping main loop...")
        main_loop.quit()
        return False
    
    # Run for 3 seconds to allow sound to play
    GLib.timeout_add(3000, quit_after_delay)
    
    print("Starting main loop...")
    try:
        main_loop.run()
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    print("Test completed.")

if __name__ == "__main__":
    test_sfx()