import gi
from gi.repository import Gtk, Gdk

def ensure_touch_css_loaded():
    """Ensure the touch tile CSS is loaded once per application."""
    if getattr(ensure_touch_css_loaded, '_css_loaded', False):
        return
    css = b'''
    .touch_tile_green {
        background: #4caf50;
        color: #fff;
        min-height: 50px;
        margin-bottom: 10px;
    }
    .touch_tile_blue {
        background: #90caf9;
        color: #fff;
        min-height: 50px;
        margin-bottom: 10px;
    }
    .touch_tile_red {
        background: #e53935;
        color: #fff;
        min-height: 50px;
        margin-bottom: 10px;
    }
    .touch_tile_yellow {
        background: #ffd600;
        color: #000;
        min-height: 50px;
        margin-bottom: 10px;
    }
    .touch_tile_orange {
        background: #ffb300;
        color: #000;
        min-height: 50px;
        margin-bottom: 10px;
    }
    '''
    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    ensure_touch_css_loaded._css_loaded = True

def set_touch_tile_color(button, color):
    """
    Set the appearance of a button to a primary color.
    Args:
        button (Gtk.Button): The button to update.
        color (str): One of 'green', 'blue', 'red', 'yellow', 'orange'.
    """
    allowed = {"green", "blue", "red", "yellow", "orange"}
    if color not in allowed:
        raise ValueError(f"Unsupported color: {color}")
    style_context = button.get_style_context()
    # Remove all possible tile color classes
    for c in allowed:
        style_context.remove_class(f"touch_tile_{c}")
    style_context.add_class(f"touch_tile_{color}")
