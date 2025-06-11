# -*- coding: utf-8 -*-
# touch.py - Graphics tools for touch UI enhancements in Quod Libet.
# Copyright (C) 2025 John Dykstra.
# This file is part of Quod Libet. See LICENSE for details.

import gi
from gi.repository import Gtk, Gdk

def ensure_touch_css_loaded():
    """Ensure the touch CSS is loaded once per application."""
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

class TouchTile(Gtk.Button):
    GREEN = "green"
    BLUE = "blue"
    RED = "red"
    YELLOW = "yellow"
    ORANGE = "orange"
    _VALID_COLORS = {
        GREEN,
        BLUE,
        RED,
        YELLOW,
        ORANGE,
    }

    def __init__(self, label=None, color=GREEN, **kwargs):
        ensure_touch_css_loaded()
        super().__init__(label=label, **kwargs)
        
        #  ??  Shouldn't this be in the CSS?
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_size_request(-1, 25)

        self.set_color(color)

    def set_color(self, color):
        """
        Set the appearance of the button to a primary color.
        Args:
            color (str): One of 'green', 'blue', 'red', 'yellow', 'orange'.
        """
        if color not in self._VALID_COLORS:
            raise ValueError(f"Unsupported color: {color}")
        style_context = self.get_style_context()
        for c in self._VALID_COLORS:
            style_context.remove_class(f"touch_tile_{c}")
        style_context.add_class(f"touch_tile_{color}")

