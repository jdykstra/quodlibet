import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from quodlibet import qltk
from quodlibet.qltk.menubutton import MenuButton
from quodlibet.qltk.touch import ensure_touch_css_loaded, set_touch_tile_color

from ..player.dsp import DspController, dsp_controller

class ConfigSelector(Gtk.VBox):
    def __init__(self, browser):
        super().__init__(spacing=10)
        self.browser = browser
        
        self.selected_config = None
        ensure_touch_css_loaded()

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
        self.create_config_chooser()
        for button in self.rect_buttons:
            self.config_buttons_box.pack_start(button, False, False, 0)
        self.pack_start(self.config_buttons_box, False, False, 0)

    def create_config_chooser(self):
        """
        Create rectangle buttons for each configuration file, colored red if unselected and green if selected.
        """
        try:
            dsp_controller.connect()
            self.config_dir, config_files = dsp_controller.get_configs()
            current_path = dsp_controller.config.file_path()
            current_file = os.path.basename(current_path) if current_path else None
        except Exception as e:
            error_label = Gtk.Label(label=f"Error: {e}")
            self.pack_start(error_label, False, False, 0)
            return
        finally:
            dsp_controller.disconnect()
            
        self.rect_buttons = []
        self.button_to_config = {}
        config_files = list(config_files)  
        for config_file in config_files:
            button = Gtk.Button(label=config_file)
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.set_size_request(-1, 25)
            button.connect("clicked", self.on_rect_button_clicked, config_file)
            self.rect_buttons.append(button)
            self.button_to_config[button] = config_file

        # Select the button matching the current config file, if any
        #  ??  Change the color, but don't command the DSP.
        #  ??  There's got to be a a way to do with with button_to_config.
        selected_button = None
        for button, config_file in self.button_to_config.items():
            if config_file == current_file:
                selected_button = button
                break

        if selected_button:
            self.select_rect_button(selected_button, current_file)
        elif self.rect_buttons:
            self.select_rect_button(self.rect_buttons[0], config_files[0])

    def select_rect_button(self, selected_button, new_config):
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

        for button in self.rect_buttons:
            set_touch_tile_color(button, "green" if button == selected_button else "blue")
        self.selected_config = new_config

    def on_rect_button_clicked(self, button, new_config):
        self.select_rect_button(button, new_config)


class DspControlWindow(qltk.UniqueWindow):
    def __init__(self, browser):
        if self.is_not_unique():
            return
        super().__init__()
        self.set_transient_for(qltk.get_top_parent(browser))
        self.set_default_size(350, 200)
        self.set_border_width(12)
        self.set_title("Camilla DSP")
        vbox = ConfigSelector(browser)
        self.add(vbox)
        self.get_child().show_all()

class DspWindowButton(Gtk.HBox):
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
