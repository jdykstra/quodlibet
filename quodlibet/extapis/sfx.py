import importlib.resources
import sys
from quodlibet.util.dprint import print_e, print_d
from quodlibet import config

try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import GLib, Gst
    # Initialize GStreamer if not already done
    if not Gst.is_initialized():
        Gst.init(None)
except ImportError:
    GLib = None
    Gst = None


"""  
Mappings from SFX names to their files in quodlibet/sounds. 
"""
POWER_UP = "startup_harp_arpeggio"
POWER_DOWN = "shutdown_harp_arpeggio"


def _create_sfx_pipeline(audio_sink=None):
    """Create a GStreamer pipeline for sound effects.
    
    Args:
        audio_sink: Specific audio sink (e.g., "pulsesink device=alsa_output.platform-snd_aloop.0.analog-stereo")
                   If None, uses system default
    
    Returns:
        Gst.Pipeline or None if creation failed
    """
    if Gst is None:
        return None
    
    pipeline = Gst.Pipeline.new("sfx-pipeline")
    
    # Create elements
    filesrc = Gst.ElementFactory.make("filesrc", "file-source")
    decoder = Gst.ElementFactory.make("decodebin", "decoder")
    audioconvert = Gst.ElementFactory.make("audioconvert", "audio-convert")
    audioresample = Gst.ElementFactory.make("audioresample", "audio-resample")
    
    if not all([filesrc, decoder, audioconvert, audioresample]):
        print_e("Failed to create required GStreamer elements for SFX")
        return None
    
    # Create audio sink
    if audio_sink:
        # Parse custom audio sink specification
        try:
            sink = Gst.parse_launch(audio_sink)
        except Exception as e:
            print_e(f"Failed to parse audio sink '{audio_sink}': {e}")
            sink = Gst.ElementFactory.make("autoaudiosink", "audio-sink")
    else:
        # Use default auto sink
        sink = Gst.ElementFactory.make("autoaudiosink", "audio-sink")
    
    if not sink:
        print_e("Failed to create audio sink for SFX")
        return None
    
    # Add elements to pipeline
    pipeline.add(filesrc)
    pipeline.add(decoder)
    pipeline.add(audioconvert)
    pipeline.add(audioresample)
    pipeline.add(sink)
    
    # Link static elements (decoder will be linked dynamically)
    if not filesrc.link(decoder):
        print_e("Failed to link filesrc to decoder")
        return None
    
    if not audioconvert.link(audioresample):
        print_e("Failed to link audioconvert to audioresample")
        return None
    
    if not audioresample.link(sink):
        print_e("Failed to link audioresample to sink")
        return None
    
    # Connect decoder pad-added signal for dynamic linking
    def on_pad_added(decoder, pad):
        caps = pad.get_current_caps()
        if caps:
            struct = caps.get_structure(0)
            if struct.get_name().startswith("audio/"):
                sink_pad = audioconvert.get_static_pad("sink")
                if sink_pad and not sink_pad.is_linked():
                    pad.link(sink_pad)
    
    decoder.connect("pad-added", on_pad_added)
    
    return pipeline


def play_sfx(name: str, audio_sink=None):
    """
    Play a sound effect asynchronously by name using GStreamer.
    
    Args:
        name: Sound effect name (matches WAV file in 'quodlibet/sounds' package)
        audio_sink: Optional specific audio sink (e.g., "pulsesink device=alsa_output.platform-snd_aloop.0.analog-stereo")
                   If None, uses system default audio device
    
    The sound is played through GStreamer pipeline, allowing targeting different audio devices
    than the main Quod Libet player. Returns immediately; sound plays in the background.
    """
    print_d(f"Entering play_sfx with name: {name}, sink: {audio_sink}")
    
    if Gst is None:
        print_e("GStreamer is required for sound effects playback")
        return
    
    if GLib is None:
        print_e("GLib is required for GTK main loop integration")
        return

    def _play():
        try:
            with importlib.resources.path('quodlibet.sounds', f'{name}.wav') as wav_path:
                print_d(f"Creating GStreamer pipeline for {wav_path}")
                
                # Create pipeline
                pipeline = _create_sfx_pipeline(audio_sink)
                if not pipeline:
                    print_e("Failed to create GStreamer pipeline for SFX")
                    return False
                
                # Set file source
                filesrc = pipeline.get_by_name("file-source")
                filesrc.set_property("location", str(wav_path))
                
                # Set up bus to handle messages
                bus = pipeline.get_bus()
                bus.add_signal_watch()
                
                def on_message(bus, message):
                    if message.type == Gst.MessageType.EOS:
                        print_d("SFX playback finished")
                        pipeline.set_state(Gst.State.NULL)
                        bus.remove_signal_watch()
                    elif message.type == Gst.MessageType.ERROR:
                        err, debug = message.parse_error()
                        print_e(f"SFX playback error: {err.message}")
                        if debug:
                            print_d(f"Debug info: {debug}")
                        pipeline.set_state(Gst.State.NULL)
                        bus.remove_signal_watch()
                
                bus.connect("message", on_message)
                
                # Start playback
                ret = pipeline.set_state(Gst.State.PLAYING)
                if ret == Gst.StateChangeReturn.FAILURE:
                    print_e("Failed to start SFX playback")
                    bus.remove_signal_watch()
                    return False
                
                print_d(f"SFX playback started for {name}")
                
        except FileNotFoundError:
            print_e(f"Sound effect '{name}.wav' not found in quodlibet/sounds.")
        except Exception as e:
            print_e(f"Error playing sound effect '{name}': {e}")
        
        return False  # Don't repeat this idle callback

    GLib.idle_add(_play)
    print_d("GStreamer SFX scheduled for playback in main loop")
