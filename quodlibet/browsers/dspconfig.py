import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from gi.repository import GObject

from quodlibet import qltk
from quodlibet import config
from quodlibet.qltk.menubutton import MenuButton

from ..player.dsp import DspController, dsp_controller
import quodlibet.qltk.touch as tt


class ConfigChooser(Gtk.VBox):

    SELECTED_COLOR = tt.TouchTile.GREEN
    UNSELECTED_COLOR = tt.TouchTile.BLUE

    def __init__(self, browser):
        super().__init__(spacing=10)
        self.browser = browser
        
        self.selected_config = None
        tt.ensure_touch_css_loaded()

        # Create a label
        label = Gtk.Label(label="Active Configuration")
        label_box = Gtk.HBox()
        label.set_justify(Gtk.Justification.CENTER)
        label.set_alignment(0.5, 0.5)
        label_box.pack_start(label, True, True, 0)
        self.pack_start(label_box, False, False, 0)

        # Create a container for config buttons in a scrolled window.
        self.rect_buttons = []
        self.button_to_config = {}
        self.config_buttons_box = Gtk.VBox()
        
        # Create a scrolled window for the config buttons
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(100)
        scrolled_window.set_max_content_height(300)
        scrolled_window.add(self.config_buttons_box)
        
        self._create_buttons()
        self.pack_start(scrolled_window, True, True, 0)

    def _create_buttons(self):
        """
        Create rectangle buttons for each configuration file, colored red if unselected and green if selected.
        """
        try:
            dsp_controller.connect()
            self.config_dir, config_files = dsp_controller.get_configs()
            self.config_files = sorted(config_files)
            current_path = dsp_controller.config.file_path()
            self._current_config = os.path.basename(current_path) if current_path else None

            self._configs = {}
            for f in self.config_files:
                config = dsp_controller.config.read_and_parse_file(os.path.join(self.config_dir, f))
                self._configs[f] = config
                button = tt.TouchTile(label=config.get("title", f), color=self.UNSELECTED_COLOR)
                if f == self._current_config:
                    button.set_color(self.SELECTED_COLOR)
                    self._selected_button = button
                button.connect("clicked", self._on_rect_button_clicked, f)
                self.config_buttons_box.pack_start(button, False, False, 0)

        except Exception as e:
            error_label = Gtk.Label(label=f"Error: {e}")
            self.pack_start(error_label, False, False, 0)
            return
        finally:
            dsp_controller.disconnect()



    def _change_selected_config(self, selected_button, new_config):
        try:
            dsp_controller.connect()
            dsp_controller.config.set_file_path(os.path.join(self.config_dir, new_config))
            dsp_controller.general.reload()
            print(f"Configuration '{new_config}' applied successfully.")
        except Exception as e:
            print(f"Failed to apply configuration {new_config}: {e}")
            return
        finally:
            dsp_controller.disconnect()


    def _on_rect_button_clicked(self, button, new_config):
        self._change_selected_config(button, new_config)
        if self._selected_button:
            self._selected_button.set_color(self.UNSELECTED_COLOR)
        button.set_color(self.SELECTED_COLOR)    
        self._current_config = new_config
        self._selected_button = button


class DspStatusPane(Gtk.VBox):
    """
    Pane to display the current DSP status as a TouchTile.
    """
    STATE_COLORS = {
        "running": tt.TouchTile.GREEN,
        "starting": tt.TouchTile.YELLOW,
        "stalled": tt.TouchTile.RED,
        "paused": tt.TouchTile.BLUE,
        "inactive": tt.TouchTile.ORANGE,
    }

    def __init__(self):
        super().__init__(spacing=10)
        tt.ensure_touch_css_loaded()
        # Add a label above the TouchTile
        label = Gtk.Label(label="Status")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_alignment(0.5, 0.5)
        self.pack_start(label, False, False, 0)
        self.status_tile = tt.TouchTile(label="...", color=tt.TouchTile.BLUE)
        self.pack_start(self.status_tile, False, False, 0)
        self._refresh_id = None
        self.update_status()
        self.start_auto_refresh()  # Start auto-refresh immediately

    def update_status(self):
        try:
            dsp_controller.connect()
            state = dsp_controller.general.state()
            state_str = getattr(state, 'name', str(state)).lower()  # Ensure lowercase
            color = self.STATE_COLORS.get(state_str, tt.TouchTile.BLUE)
            self.status_tile.set_label(state_str.title())  # Display with proper case
            
            # Force the color change and redraw
            old_color = getattr(self.status_tile, '_current_color', None)
            self.status_tile.set_color(color)
            self.status_tile._current_color = color
            
            # Force a redraw
            self.status_tile.queue_draw()
            
            print(f"Status updated: {state_str} -> {color} (was {old_color})")  # Debug output
        except Exception as e:
            self.status_tile.set_label("Error")
            self.status_tile.set_color(tt.TouchTile.RED)
            self.status_tile.queue_draw()
            print(f"Status update error: {e}")  # Debug output
        finally:
            dsp_controller.disconnect()

    def start_auto_refresh(self):
        if self._refresh_id is None:
            self._refresh_id = GObject.timeout_add(1000, self._on_timeout)

    def stop_auto_refresh(self):
        if self._refresh_id is not None:
            GObject.source_remove(self._refresh_id)
            self._refresh_id = None

    def _on_timeout(self):
        self.update_status()
        return True  # Continue calling


class DspControlWindow(qltk.UniqueWindow):
    def __init__(self, browser):
        if self.is_not_unique():
            return
        super().__init__()
        self.set_transient_for(qltk.get_top_parent(browser))
        
        # Load persistent size and position
        width = config.getint("browsers", "dsp_window_width", 450)
        height = config.getint("browsers", "dsp_window_height", 300)
        self.set_default_size(width, height)
        
        # Load persistent position if available
        try:
            x = config.getint("browsers", "dsp_window_x")
            y = config.getint("browsers", "dsp_window_y")
            self.move(x, y)
        except config.Error:
            pass  # Use default positioning
            
        self.set_border_width(12)
        self.set_title("Camilla DSP")
        
        # Create a horizontal box to hold the status pane and config chooser
        hbox = Gtk.HBox(spacing=12)
        self.status_pane = DspStatusPane()
        hbox.pack_start(self.status_pane, False, False, 0)
        configChooser = ConfigChooser(browser)
        # Make config chooser fill vertically to match status pane height
        hbox.pack_start(configChooser, True, True, 0)
        self.add(hbox)
        self.get_child().show_all()
        
        # Connect signals for saving window state
        self.connect("destroy", self._on_destroy)
        self.connect("configure-event", self._on_configure)

    def _on_configure(self, widget, event):
        """Save window size and position when changed"""
        config.set("browsers", "dsp_window_width", event.width)
        config.set("browsers", "dsp_window_height", event.height)
        config.set("browsers", "dsp_window_x", event.x)
        config.set("browsers", "dsp_window_y", event.y)
        return False

    def _on_destroy(self, *args):
        self.status_pane.stop_auto_refresh()


class DspWindowOpener(Gtk.HBox):
    """
    Click this button to open the DSP configuration window.
    """
    def __init__(self, browser):
        super().__init__()

        # Create a regular button with an icon and label
        button = Gtk.Button()
        box = Gtk.HBox(spacing=6)
        icon = Gtk.Image.new_from_icon_name("audio-speakers-symbolic", Gtk.IconSize.BUTTON)
        box.pack_start(icon, False, False, 0)
        label = Gtk.Label(label="DSP")
        box.pack_start(label, False, False, 0)
        button.add(box)
        button.show_all()

        def on_button_clicked(widget):
            window = DspControlWindow(browser)
            window.show()
        button.connect("clicked", on_button_clicked)

        self.pack_start(button, True, True, 0)
