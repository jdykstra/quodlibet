import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from quodlibet import qltk
from quodlibet.qltk.menubutton import MenuButton

from ..player.dsp import DspController, dsp_controller

class ConfigSelector(Gtk.VBox):
    def __init__(self, dsp_controller):
        super().__init__(spacing=10)
        self.dsp_controller = dsp_controller
        self.selected_config = None

        # Create a label
        label = Gtk.Label(label="DSP Configuration File:")
        self.pack_start(label, False, False, 0)

        # Create a container for radio buttons
        self.radio_buttons = []
        self.create_radio_buttons()

        # Create an "Apply" button
        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.on_apply_clicked)
        self.pack_start(apply_button, False, False, 0)

    def create_radio_buttons(self):
        """
        Create radio buttons for each configuration file.
        """
        try:
            dsp.dsp_controller.connect()
            self.config_dir, config_files = dsp.dsp_controller.get_configs()
        except Exception as e:
            error_label = Gtk.Label(label=f"Error: {e}")
            self.pack_start(error_label, False, False, 0)
            return

        previous_button = None
        for config_file in config_files:
            button = Gtk.RadioButton.new_with_label_from_widget(previous_button, config_file)
            button.connect("toggled", self.on_radio_button_toggled, config_file)
            self.pack_start(button, False, False, 0)
            self.radio_buttons.append(button)
            previous_button = button

    def on_radio_button_toggled(self, button, config_file):
        """
        Handle radio button toggling.
        """
        if button.get_active():
            self.selected_config = config_file

    def on_apply_clicked(self, button):
        """
        Apply the selected configuration.
        """
        if self.selected_config:
            try:
                dsp.dsp_controller.set_file_path(os.path.join(self.config_dir, self.selected_config))
                dsp.dsp_controller.reload()
                print(f"Configuration '{self.selected_config}' applied successfully.")
            except Exception as e:
                print(f"Failed to apply configuration: {e}")
        else:
            print("No configuration selected.")

class DspConfigwindow(qltk.UniqueWindow):
    
    def __init__(self, browser):
        if self.is_not_unique():
            return
        super().__init__()

        self.set_transient_for(qltk.get_top_parent(browser))
        self.set_default_size(350, 300)
        self.set_border_width(12)

        self.set_title(_("DSP"))

        vbox = Gtk.VBox(spacing=12)

        column_modes = ConfigSelector(browser)

        apply_ = qltk.x.Button(_("_Apply"))

        cancel = qltk.x.Button(_("_Cancel"))
        cancel.connect("clicked", lambda x: self.destroy())

        box = Gtk.HButtonBox()
        box.set_spacing(6)
        box.set_layout(Gtk.ButtonBoxStyle.EDGE)
        box.pack_start(apply_, False, False, 0)
        box.pack_start(cancel, True, True, 0)

        vbox.pack_start(box, False, True, 0)
        self.add(vbox)

        cancel.grab_focus()
        self.get_child().show_all()

class DspButton(Gtk.HBox):
    def __init__(self, browser):
        super().__init__()

        self._menu = menu = Gtk.Menu()

        pref_item = qltk.x.MenuItem("_Dsp Menu", Icons.PREFERENCES_SYSTEM)

        def config_cb(menu_item):
            window = DspConfigwindow(browser)
            window.show()
        pref_item.connect("activate", config_cb)
        menu.append(pref_item)

        menu.show_all()

        button = qltk.menubutton.MenuButton(
                qltk.x.SymbolicIconImage(qltk.Icons.EMBLEM_SYSTEM, Gtk.IconSize.MENU),
                arrow=True)
        button.set_menu(menu)
        button.show()
        self.pack_start(button, True, True, 0)
