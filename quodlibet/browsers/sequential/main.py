from __future__ import annotations

from dataclasses import dataclass

from gi.repository import GLib, Gtk, Pango

from quodlibet import _
from quodlibet import app
from quodlibet import config
from quodlibet import qltk
from quodlibet.browsers import Browser
from quodlibet.formats import PEOPLE
from quodlibet.qltk import is_accel
from quodlibet.qltk.completion import LibraryTagCompletion
from quodlibet.qltk.searchbar import SearchBarBox
from quodlibet.qltk.songlist import SongList
from quodlibet.qltk.views import AllTreeView, TreeViewColumnButton
from quodlibet.qltk.x import Align, ScrolledWindow
from quodlibet.util.library import background_filter


LEVELS = ("genre", "artist", "album", "song")
PATH_LEVELS = LEVELS[:-1]
LEVEL_TITLES = {
    "genre": _("Genres"),
    "artist": _("Artists"),
    "album": _("Albums"),
    "song": _("Songs"),
}
UNKNOWN_VALUE = "__sequential_unknown__"


@dataclass(order=True)
class DrilldownRow:
    sort_text: str
    key: str
    label: str
    count: int

    @classmethod
    def create(cls, key: str, label: str, count: int) -> "DrilldownRow":
        unknown_sort = "\uffff" if key == UNKNOWN_VALUE else ""
        return cls(f"{unknown_sort}{label.casefold()}", key, label, count)

    def get_markup(self) -> str:
        text = GLib.markup_escape_text(self.label)
        return "%s <span alpha='60%%'>(%d)</span>" % (text, self.count)

    def contains_text(self, text: str) -> bool:
        return text.casefold() in self.label.casefold()


class DrilldownView(AllTreeView):

    def __init__(self):
        super().__init__()
        self.set_fixed_height_mode(True)
        self.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        column = TreeViewColumnButton(title="")
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column.set_fixed_width(60)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column.pack_start(renderer, True)

        def text_cdf(column, cell, model, iter_, data):
            row = model.get_value(iter_, 0)
            cell.set_property("markup", row.get_markup())

        column.set_cell_data_func(renderer, text_cdf)
        self.append_column(column)
        self._column = column

        self.set_model(Gtk.ListStore(object))
        self.set_search_equal_func(self.__search_func, None)
        self.set_search_column(0)
        self.set_enable_search(True)

    def __search_func(self, model, column, key, iter_, data):
        row = model.get_value(iter_, 0)
        return not row.contains_text(key)

    def set_title(self, title: str) -> None:
        self._column.set_title(title)

    def set_rows(self, rows: list[DrilldownRow], selected_key: str | None) -> None:
        model = self.get_model()
        model.clear()
        selected_path = None
        for index, row in enumerate(rows):
            model.append([row])
            if row.key == selected_key:
                selected_path = Gtk.TreePath((index,))

        self.get_selection().unselect_all()
        if selected_path is not None:
            self.set_cursor(selected_path)
        elif rows:
            self.set_cursor(Gtk.TreePath((0,)))

    def get_selected_row(self) -> DrilldownRow | None:
        model, iter_ = self.get_selection().get_selected()
        if iter_ is None:
            return None
        return model.get_value(iter_, 0)

    def get_row_labels(self) -> list[str]:
        return [row[0].label for row in self.get_model()]


class SequentialBrowser(Browser):
    name = _("Sequential Browser")
    accelerated_name = _("_Sequential Browser")
    keys = ["Sequential", "SequentialBrowser"]
    priority = 5

    def __init__(self, library):
        super().__init__(spacing=6, orientation=Gtk.Orientation.VERTICAL)

        self._library = library
        self._query = None
        self._query_filter = lambda song: True
        self._level_index = 0
        self._path_values = {tag: None for tag in PATH_LEVELS}
        self._songpane = None

        completion = LibraryTagCompletion(library.librarian)
        self.accelerators = Gtk.AccelGroup()
        search = SearchBarBox(completion=completion,
                              accel_group=self.accelerators)
        search.connect("query-changed", self.__text_parse)
        search.connect("focus-out", self.__focus)
        search.connect("key-press-event", self.__search_key_pressed)
        self._search = search
        self.pack_start(Align(search, left=6, right=6), False, True, 0)

        header = Gtk.Box(spacing=3, orientation=Gtk.Orientation.VERTICAL)
        breadcrumb_box = Gtk.Box(spacing=6, homogeneous=False)
        self._breadcrumb_box = breadcrumb_box
        self._breadcrumb_buttons = {}
        self._breadcrumb_slots = {}
        for index, tag in enumerate(PATH_LEVELS):
            slot = Gtk.Box()
            button = Gtk.Button(label=tag)
            button.set_size_request(52, 52)
            button.set_relief(Gtk.ReliefStyle.NONE)
            child = button.get_child()
            if isinstance(child, Gtk.Label):
                child.set_ellipsize(Pango.EllipsizeMode.END)
                child.set_single_line_mode(True)
                child.set_max_width_chars(24)
            button.connect("clicked", self.__breadcrumb_clicked, index)
            slot.pack_start(button, True, True, 0)
            breadcrumb_box.pack_start(slot, True, True, 0)
            self._breadcrumb_buttons[tag] = button
            self._breadcrumb_slots[tag] = slot
        header.pack_start(breadcrumb_box, True, True, 0)

        breadcrumb_label = Gtk.Label(xalign=0.0)
        breadcrumb_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        breadcrumb_label.get_style_context().add_class("dim-label")
        self._breadcrumb_label = breadcrumb_label
        header.pack_start(breadcrumb_label, False, True, 0)
        self.pack_start(Align(header, left=6, right=6), False, True, 0)

        self._view = DrilldownView()
        self._view.connect("row-activated", self.__row_activated)
        self._view.connect("selection-changed", self.__selection_changed)
        scrolled = ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.add(self._view)
        self._browser_page = scrolled

        self._stack = Gtk.Stack()
        self._stack.add_named(self._browser_page, "browser")
        self.pack_start(self._stack, True, True, 0)
        self.show_all()
        self.__refresh_view()

    def pack(self, songpane):
        container = Gtk.HBox()
        container.pack_start(self, True, True, 0)
        songpane_was_visible = songpane.get_visible()

        if songpane.get_parent() is not None:
            songpane.get_parent().remove(songpane)
        self._songpane = songpane
        self._stack.add_named(songpane, "songs")
        container.show_all()
        if not songpane_was_visible:
            songpane.hide()
        self.__sync_page()
        GLib.idle_add(self.__sync_page)
        return container

    def unpack(self, container, songpane):
        if self._songpane is songpane:
            self._stack.remove(songpane)
            self._songpane = None
        container.remove(self)

    def _get_text(self):
        return self._search.get_text()

    def _set_text(self, text):
        self._search.set_text(text)

    def __focus(self, widget, *args):
        top = qltk.get_top_parent(widget)
        if hasattr(top, "songlist"):
            top.songlist.grab_focus()

    def __text_parse(self, bar, text):
        self.activate()

    def __search_key_pressed(self, entry, event):
        if (is_accel(event, "<Primary>Return") or
                is_accel(event, "<Primary>KP_Enter")):
            songs = app.window.songlist.get_songs()
            limit = config.getint("browsers", "searchbar_enqueue_limit")
            app.window.enqueue(songs, limit)
            return True
        return False

    def __selection_changed(self, *args):
        self.__update_header()

    def __row_activated(self, view, path, column):
        if self._level_index >= len(PATH_LEVELS):
            return
        row = self._view.get_selected_row()
        if row is None:
            return

        current_tag = PATH_LEVELS[self._level_index]
        self._path_values[current_tag] = row.key
        self.__clear_deeper(self._level_index + 1)
        self._level_index = min(self._level_index + 1, len(LEVELS) - 1)
        self.activate()

    def __breadcrumb_clicked(self, button, level_index):
        if level_index >= self._level_index:
            return
        self._level_index = level_index
        self._path_values[PATH_LEVELS[level_index]] = None
        self.__clear_deeper(level_index + 1)
        self.activate()

    def __clear_deeper(self, start_index: int) -> None:
        for tag in PATH_LEVELS[start_index:]:
            self._path_values[tag] = None

    def __sync_page(self) -> None:
        page = self._songpane if self._level_index == len(PATH_LEVELS) and self._songpane else self._browser_page
        self._stack.set_visible_child(page)

    def __update_header(self) -> None:
        current_level = LEVELS[self._level_index]
        self._view.set_title("")
        values = []
        for index, tag in enumerate(PATH_LEVELS):
            value = self._path_values[tag]
            if value is not None:
                values.append(self.__display_value(value))
            button = self._breadcrumb_buttons[tag]
            button.set_label(tag)
            button.set_tooltip_text(tag)
            is_visible = index < self._level_index
            button.set_visible(is_visible)
            button.set_sensitive(is_visible)
        self._breadcrumb_label.set_text(" / ".join(values))

    def __display_value(self, value: str) -> str:
        if value == UNKNOWN_VALUE:
            return _("Unknown")
        return value

    def __normalize_navigation(self, songs):
        normalized_songs = list(songs)
        for index, tag in enumerate(PATH_LEVELS):
            value = self._path_values[tag]
            if index >= self._level_index:
                break
            if value is None:
                self._level_index = index
                self.__clear_deeper(index)
                break
            available_keys = {row.key for row in self.__build_rows(tag, normalized_songs)}
            if value not in available_keys:
                self._level_index = index
                self._path_values[tag] = None
                self.__clear_deeper(index + 1)
                break
            normalized_songs = self.__filter_songs_for_value(normalized_songs, tag, value)

    def __base_songs(self):
        star = dict.fromkeys(SongList.star)
        star.update(dict.fromkeys(PEOPLE))
        query = self._search.get_query(star.keys())
        self._query = query if query.is_parsable else None
        self._query_filter = query.search if query.is_parsable else (lambda song: True)
        songs = list(filter(self._query_filter, self._library))
        bg = background_filter()
        if bg:
            songs = list(filter(bg, songs))
        return songs

    def __songs_for_depth(self, depth: int):
        songs = self.__base_songs()
        self.__normalize_navigation(songs)
        for tag in PATH_LEVELS[:depth]:
            value = self._path_values[tag]
            if value is None:
                break
            songs = self.__filter_songs_for_value(songs, tag, value)
        return songs

    def __filter_songs_for_value(self, songs, tag: str, value: str):
        return [song for song in songs if self.__song_matches_value(song, tag, value)]

    def __song_matches_value(self, song, tag: str, value: str) -> bool:
        values = [item for item in song.list(tag) if item]
        if value == UNKNOWN_VALUE:
            return not values
        return value in values

    def __build_rows(self, tag: str, songs) -> list[DrilldownRow]:
        grouped = {}
        for song in songs:
            values = [item for item in song.list(tag) if item] or [UNKNOWN_VALUE]
            for value in values:
                grouped.setdefault(value, []).append(song)

        rows = []
        for key, grouped_songs in grouped.items():
            rows.append(DrilldownRow.create(
                key,
                self.__display_value(key),
                len(grouped_songs)))
        rows.sort()
        return rows

    def __refresh_view(self) -> None:
        current_level = LEVELS[self._level_index]
        if current_level == "song":
            songs = self.__songs_for_depth(len(PATH_LEVELS))
            GLib.idle_add(self.songs_selected, songs)
        else:
            songs = self.__songs_for_depth(self._level_index)
            tag = PATH_LEVELS[self._level_index]
            rows = self.__build_rows(tag, songs)
            self._view.set_rows(rows, self._path_values[tag])
        self.__sync_page()
        self.__update_header()

    def activate(self):
        self.__refresh_view()

    def save(self):
        config.settext("browsers", "query_text", self._get_text())
        config.settext("browsers", "sequential_browser_level",
                       LEVELS[self._level_index])
        parts = []
        for tag in PATH_LEVELS:
            value = self._path_values[tag]
            if value is None:
                continue
            parts.append(f"{tag}={value}")
        config.settext("browsers", "sequential_browser_path", "\n".join(parts))

    def restore(self):
        self._set_text(config.gettext("browsers", "query_text"))
        level_name = config.gettext("browsers", "sequential_browser_level", LEVELS[0])
        self._level_index = LEVELS.index(level_name) if level_name in LEVELS else 0
        path_text = config.gettext("browsers", "sequential_browser_path", "")
        self._path_values = {tag: None for tag in PATH_LEVELS}
        for line in path_text.splitlines():
            if "=" not in line:
                continue
            tag, value = line.split("=", 1)
            if tag in self._path_values:
                self._path_values[tag] = value

    def finalize(self, restored):
        config.settext("browsers", "query_text", "")

    def can_filter_text(self):
        return True

    def filter_text(self, text):
        self._set_text(text)
        self.activate()

    def get_filter_text(self):
        return self._get_text()

    def can_filter_tag(self, tag):
        return tag in PATH_LEVELS or tag in PEOPLE

    def filter(self, tag, values):
        if tag in PEOPLE:
            tag = "artist"
        if tag not in PATH_LEVELS:
            return
        chosen = next(iter(values), None)
        level_index = PATH_LEVELS.index(tag)
        self._path_values[tag] = chosen
        self.__clear_deeper(level_index + 1)
        self._level_index = min(level_index + 1, len(LEVELS) - 1)
        self.activate()

    def list(self, tag):
        if tag in PEOPLE:
            tag = "artist"
        if tag not in PATH_LEVELS:
            return super().list(tag)
        songs = self.__songs_for_depth(PATH_LEVELS.index(tag))
        return [row.key for row in self.__build_rows(tag, songs)]

    def unfilter(self):
        self._set_text("")
        self._level_index = 0
        self._path_values = {tag: None for tag in PATH_LEVELS}
        self.activate()

    def active_filter(self, song):
        if not self._query_filter(song):
            return False
        for tag in PATH_LEVELS:
            value = self._path_values[tag]
            if value is None:
                continue
            if not self.__song_matches_value(song, tag, value):
                return False
        return True