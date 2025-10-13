import importlib.resources
import threading
import sys
from quodlibet.util.dprint import print_e

try:
    import simpleaudio as sa
except ImportError:
    sa = None


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
    Returns immediately; sound plays in the background.
    """
    if sa is None:
        print_e("simpleaudio is required for sound playback. Install with: pip install simpleaudio")
        return

    def _play():
        try:
            with importlib.resources.path('quodlibet.sounds', f'{name}.wav') as wav_path:
                wave_obj = sa.WaveObject.from_wave_file(str(wav_path))
                wave_obj.play()  # Play asynchronously
        except FileNotFoundError:
            print_e(f"Sound effect '{name}.wav' not found in quodlibet/sounds.")
        except Exception as e:
            print_e(f"Error playing sound effect '{name}': {e}")

    threading.Thread(target=_play, daemon=True).start()
