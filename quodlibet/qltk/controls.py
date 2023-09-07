# Copyright 2004-2005 Joe Wreschnig, Michael Urman, Iñigo Serna
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from gi.repository import Gtk, Gdk, GObject

from quodlibet import config
from quodlibet import qltk
from quodlibet import _
from quodlibet.util import connect_obj, connect_destroy
from quodlibet.qltk.x import SymbolicIconImage
from quodlibet.qltk.util import GSignals
from quodlibet.qltk.seekbutton import SeekButton
from quodlibet.util.dprint import print_e





class PlayPauseButton(Gtk.Button):

    __gsignals__: GSignals = {
        "toggled": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__(relief=Gtk.ReliefStyle.NONE)
        self._pause_image = SymbolicIconImage("media-playback-pause",
                                               Gtk.IconSize.LARGE_TOOLBAR)
        self._play_image = SymbolicIconImage("media-playback-start",
                                             Gtk.IconSize.LARGE_TOOLBAR)
        self._set_active(False)
        self.connect("clicked", self._on_clicked)

    def _on_clicked(self, *args):
        self.set_active(not self.get_active())

    def _set_active(self, is_active):
        if self.get_child():
            self.remove(self.get_child())

        if is_active:
            self.add(self._pause_image)
        else:
            self.add(self._play_image)
        self.get_child().show()

        self.emit("toggled")

    def set_active(self, is_active):
        if self.get_active() == is_active:
            return
        config.set("player", "is_playing", is_active)
        self._set_active(is_active)

    def get_active(self):
        return self.get_child() is self._pause_image


class PlayControls(Gtk.VBox):

    def __init__(self, player, library):
        super().__init__(spacing=3)

        upper = Gtk.Table(n_rows=1, n_columns=3, homogeneous=True)
        upper.set_row_spacings(3)
        upper.set_col_spacings(3)

        prev = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        prev.add(SymbolicIconImage("media-skip-backward",
                                   Gtk.IconSize.LARGE_TOOLBAR))
        upper.attach(prev, 0, 1, 0, 1)

        play = PlayPauseButton()
        upper.attach(play, 1, 2, 0, 1)

        next_ = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        next_.add(SymbolicIconImage("media-skip-forward",
                                    Gtk.IconSize.LARGE_TOOLBAR))
        upper.attach(next_, 2, 3, 0, 1)
        self.pack_start(upper, False, True, 0)
        
        connect_obj(prev, 'clicked', self.__previous, player)
        self._toggle_id = play.connect('toggled', self.__playpause, player)
        play.add_events(Gdk.EventMask.SCROLL_MASK)
        connect_obj(play, "scroll-event", self.__scroll, player)
        connect_obj(next_, "clicked", self.__next, player)
        connect_destroy(
            player, "song-started", self.__song_started, next_, play)
        connect_destroy(
            player, "paused", self.__on_set_paused_unpaused, play, False)
        connect_destroy(
            player, "unpaused", self.__on_set_paused_unpaused, play, True)

    def __on_set_paused_unpaused(self, player, button, state):
        # block to prevent a signal cycle in case the paused signal and state
        # get out of sync (shouldn't happen.. but)
        button.handler_block(self._toggle_id)
        button.set_active(state)
        button.handler_unblock(self._toggle_id)

    def __scroll(self, player, event):
        if event.direction in [Gdk.ScrollDirection.UP,
                               Gdk.ScrollDirection.LEFT]:
            player.previous()
        elif event.direction in [Gdk.ScrollDirection.DOWN,
                                 Gdk.ScrollDirection.RIGHT]:
            player.next()

    def __song_started(self, player, song, next, play):
        play.set_active(not player.paused)

    def __playpause(self, button, player):
        if button.get_active():
            player.play()
        else:
            player.paused = True

    def __previous(self, player):
        player.previous()

    def __next(self, player):
        player.next()
