# Copyright 2005 Joe Wreschnig, Michael Urman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# $Id$

# Widget wrappers for GTK.
import os, sys
import gobject, gtk, pango
import config
import util

def get_top_parent(widget):
    """Return the ultimate parent of a widget; the assumption that code
    using this makes is that it will be a gtk.Window, i.e. the widget
    is fully packed when this is called."""
    if widget is not None:
        while widget.parent is not None: widget = widget.parent
    return widget

# Legacy plugin/code support.
from qltk.msg import *
from qltk.x import *
from qltk.getstring import GetStringDialog

class DeleteDialog(gtk.Dialog):
    def __init__(self, files):
        gtk.Dialog.__init__(self, _("Delete Files"))
        self.set_border_width(6)
        self.vbox.set_spacing(6)
        self.set_has_separator(False)
        self.action_area.set_border_width(0)
        self.set_resizable(False)
        # This is the GNOME trash can for at least some versions.
        # The FreeDesktop spec is complicated and I'm not sure it's
        # actually used by anything.
        if os.path.isdir(os.path.expanduser("~/.Trash")):
            b = Button(_("_Move to Trash"), gtk.STOCK_DELETE)
            self.add_action_widget(b, 0)

        self.add_button(gtk.STOCK_CANCEL, 1)
        self.add_button(gtk.STOCK_DELETE, 2)

        hbox = gtk.HBox()
        hbox.set_border_width(6)
        i = gtk.Image()
        i.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        i.set_padding(12, 0)
        i.set_alignment(0.5, 0.0)
        hbox.pack_start(i, expand=False)
        vbox = gtk.VBox(spacing=6)
        base = os.path.basename(files[0])
        if len(files) == 1: l = _("Permanently delete this file?")
        else: l = _("Permanently delete these files?")
        if len(files) == 1:
            exp = gtk.Expander("%s" % util.fsdecode(base))
        else:
            exp = gtk.Expander(ngettext("%(title)s and %(count)d more...",
                "%(title)s and %(count)d more...", len(files)-1) %
                {'title': util.fsdecode(base), 'count': len(files) - 1})

        lab = gtk.Label()
        lab.set_markup("<big><b>%s</b></big>" % l)
        lab.set_alignment(0.0, 0.5)
        vbox.pack_start(lab, expand=False)

        lab = gtk.Label("\n".join(
            map(util.fsdecode, map(util.unexpand, files))))
        lab.set_alignment(0.1, 0.0)
        exp.add(gtk.ScrolledWindow())
        exp.child.add_with_viewport(lab)
        exp.child.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        exp.child.child.set_shadow_type(gtk.SHADOW_NONE)
        vbox.pack_start(exp)
        hbox.pack_start(vbox)
        self.vbox.pack_start(hbox)
        self.vbox.show_all()

class ConfigCheckButton(gtk.CheckButton):
    """A CheckButton that connects to QL's config module, and toggles
    a boolean configuration value when it is toggled.

    It is *not* set to the current config value initially."""

    def __init__(self, label, section, option):
        gtk.CheckButton.__init__(self, label)
        self.connect('toggled', ConfigCheckButton.__toggled, section, option)

    def __toggled(self, section, option):
        config.set(section, option, str(bool(self.get_active())).lower())

class ValidatingEntry(gtk.Entry):
    """An entry with visual feedback as to whether it is valid or not.
    The given validator function gets a string and returns True (green),
    False (red), or a color string, or None (black).

    parser.is_valid_color mimicks the behavior of the search bar.

    If the "Color search terms" option is off, the entry will not
    change color."""

    def __init__(self, validator=None, *args):
        gtk.Entry.__init__(self, *args)
        if validator: self.connect_object('changed', self.__color, validator)

    def __color(self, validator):
        if config.getboolean('browsers', 'color'):
            value = validator(self.get_text())
            if value is True: color = "dark green"
            elif value is False: color = "red"
            elif isinstance(value, str): color = value
            else: color = None

            if color and self.get_property('sensitive'):
                self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))
        else:
            self.modify_text(gtk.STATE_NORMAL, None)
