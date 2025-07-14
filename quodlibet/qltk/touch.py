# -*- coding: utf-8 -*-
# touch.py - Graphics tools for touch UI enhancements in Quod Libet.
# Copyright (C) 2025 John Dykstra.
# This file is part of Quod Libet. See LICENSE for details.

import gi
from gi.repository import Gtk, Gdk

def ensure_touch_css_loaded():
    """Ensure the touch CSS for TouchTile is loaded once per application."""
    if getattr(ensure_touch_css_loaded, '_css_loaded', False):
        return
    css = b'''
    .touch_tile {
        min-height: 50px;
        margin-bottom: 10px;
        border-radius: 8px;
        font-size: 1.1em;
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
    _VALID_COLORS = {GREEN, BLUE, RED, YELLOW, ORANGE}
    # Pre-calculate text color for each background
    _COLOR_STYLE = {
        GREEN:  ("#4caf50",  "white"),
        BLUE:   ("#90caf9",  "black"),
        RED:    ("#e53935",  "white"),
        YELLOW: ("#ffd600",  "black"),
        ORANGE: ("#ffb300",  "black"),
    }

    def __init__(self, label=None, color=GREEN, **kwargs):
        ensure_touch_css_loaded()
        super().__init__(label=label, **kwargs)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_size_request(-1, 25)
        self.get_style_context().add_class("touch_tile")
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
        # Remove any existing custom CSS providers
        if hasattr(self, '_color_provider'):
            style_context.remove_provider(self._color_provider)
        bg_color, text_color = self._COLOR_STYLE[color]
        css_override = f"""
        .touch_tile {{
            background: {bg_color};
            color: {text_color};
        }}
        """
        self._color_provider = Gtk.CssProvider()
        self._color_provider.load_from_data(css_override.encode())
        style_context.add_provider(self._color_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

