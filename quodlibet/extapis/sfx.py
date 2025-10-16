import importlib.resources
import subprocess
import sys
import shutil
from quodlibet.util.dprint import print_e, print_d

try:
    import simpleaudio as sa
except ImportError:
    sa = None

try:
    from gi.repository import GLib
except ImportError:
    GLib = None

# Check for system audio players as fallback
_PAPLAY = shutil.which("paplay")
_APLAY = shutil.which("aplay")


"""  
Mappings from SFX names to their files in quodlibet/sounds. 
Files from freesound.org.
"""
POWER_UP = "827123__xkeril__startup-sound-computer"
POWER_DOWN = "827122__xkeril__end-of-task-sound"


def play_sfx(name: str):
    """
    Play a sound effect asynchronously by name.
    The name should match a WAV file in the 'quodlibet/sounds' package (e.g., 'power_on' -> 'power_on.wav').
    The sound is played through the default audio output device.
    Returns immediately; sound plays in the background via GTK's main loop.
    """
    print_d(f"Entering play_sfx with name: {name}")
    
    if GLib is None:
        print_e("GLib is required for GTK main loop integration.")
        return

    def _play():
        try:
            with importlib.resources.path('quodlibet.sounds', f'{name}.wav') as wav_path:
                print_d(f"_play() starting for {wav_path}")
                
                # Try simpleaudio first, with fallback to system tools
                if sa is not None:
                    try:
                        wave_obj = sa.WaveObject.from_wave_file(str(wav_path))
                        wave_obj.play()  # Play asynchronously
                        print_d("simpleaudio playback started")
                        return False  # Don't repeat this idle callback
                    except Exception as e:
                        print_e(f"simpleaudio failed (possibly segfault): {e}")
                        print_d("Falling back to system audio tools")
                
                # Fallback to system audio tools
                if _PAPLAY:
                    subprocess.Popen([_PAPLAY, str(wav_path)], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                    print_d("paplay fallback used")
                elif _APLAY:
                    subprocess.Popen([_APLAY, str(wav_path)], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                    print_d("aplay fallback used")
                else:
                    print_e("No audio playback method available (simpleaudio failed, no paplay/aplay)")
                    
        except FileNotFoundError:
            print_e(f"Sound effect '{name}.wav' not found in quodlibet/sounds.")
        except Exception as e:
            print_e(f"Error playing sound effect '{name}': {e}")
        return False  # Don't repeat this idle callback

    GLib.idle_add(_play)
    print_d("Sound scheduled for playback in main loop")
