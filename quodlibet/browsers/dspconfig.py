import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from quodlibet import qltk
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

        # Create a container for config buttons.
        self.rect_buttons = []
        self.button_to_config = {}
        self.config_buttons_box = Gtk.VBox()
        self._create_buttons()
        self.pack_start(self.config_buttons_box, False, False, 0)

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
        except Exception as e:
            error_label = Gtk.Label(label=f"Error: {e}")
            self.pack_start(error_label, False, False, 0)
            return
        finally:
            dsp_controller.disconnect()
            
        for f in self.config_files:
            button = tt.TouchTile(label=f, color=self.UNSELECTED_COLOR)
            if f == self._current_config:
                button.set_color(self.SELECTED_COLOR)
                self._selected_button = button
            button.connect("clicked", self._on_rect_button_clicked, f)
            self.config_buttons_box.pack_start(button, False, False, 0)


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


class DspControlWindow(qltk.UniqueWindow):
    def __init__(self, browser):
        if self.is_not_unique():
            return
        super().__init__()
        self.set_transient_for(qltk.get_top_parent(browser))
        self.set_default_size(350, 200)
        self.set_border_width(12)
        self.set_title("Camilla DSP")
        configChooser = ConfigChooser(browser)
        self.add(configChooser)
        self.get_child().show_all()


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
