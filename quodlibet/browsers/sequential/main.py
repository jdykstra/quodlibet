from __future__ import annotations

from dataclasses import dataclass

from gi.repository import GLib, Gtk, Pango

from quodlibet import _
from quodlibet import app
from quodlibet import config
from quodlibet import qltk
from quodlibet.browsers import Browser
from quodlibet.browsers.dspconfig import DspWindowOpener
from quodlibet.formats import PEOPLE
from quodlibet.qltk import is_accel
from quodlibet.qltk.completion import LibraryTagCompletion
from quodlibet.qltk.searchbar import SearchBarBox
from quodlibet.qltk.songlist import SongList
from quodlibet.qltk.touch import CompactColorTouchButton
from quodlibet.qltk.views import AllTreeView, TreeViewColumnButton
from quodlibet.qltk.x import Align, ScrolledWindow
from quodlibet.util.library import background_filter


LEVELS = ("genre", "artist", "album", "song")
PATH_LEVELS = LEVELS[:-1]
UNKNOWN_VALUE = "__sequential_unknown__"
MAX_LABEL_CHARS = 30
GRID_COLUMN_WIDTH = 260
EXTRA_ROW_SPACING = 10


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

    def get_markup(self, max_chars: int = MAX_LABEL_CHARS) -> str:
        text = GLib.markup_escape_text(self.__display_label(max_chars))
        return "%s <span alpha='60%%'>(%d)</span>" % (text, self.count)

    def __display_label(self, max_chars: int) -> str:
        if len(self.label) <= max_chars:
            return self.label
        return self.label[:max_chars - 1] + "…"

    def contains_text(self, text: str) -> bool:
        return text.casefold() in self.label.casefold()


class DrilldownView(AllTreeView):

    def __init__(self):
        super().__init__()
        self.set_fixed_height_mode(True)
        self.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        self._rows: list[DrilldownRow] = []
        self._selected_key: str | None = None
        self._visible_columns = 1
        self._tree_columns: list[Gtk.TreeViewColumn] = []
        self.__rebuild_columns()
        self.set_search_equal_func(self.__search_func, None)
        self.set_search_column(0)
        self.set_enable_search(True)
        self.connect("size-allocate", self.__size_allocate)

    def __search_func(self, model, column, key, iter_, data):
        for column_index in range(self._visible_columns):
            row = model.get_value(iter_, column_index)
            if row is not None and row.contains_text(key):
                return False
        return True

    def __size_allocate(self, widget, allocation):
        column_count = self.__column_count_for_width(allocation.width)
        if column_count == self._visible_columns:
            return
        self._visible_columns = column_count
        self.__rebuild_columns()
        self.__populate_model()

    def __column_count_for_width(self, width: int) -> int:
        if width <= 0 or not self._rows:
            return 1
        return max(1, min(len(self._rows), width // GRID_COLUMN_WIDTH or 1))

    def __rebuild_columns(self) -> None:
        for column in self.get_columns():
            self.remove_column(column)

        self._tree_columns = []
        for column_index in range(self._visible_columns):
            column = TreeViewColumnButton(title="")
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            column.set_fixed_width(GRID_COLUMN_WIDTH)
            column.set_expand(True)

            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            renderer.set_property("width-chars", MAX_LABEL_CHARS)
            renderer.set_property("ypad", EXTRA_ROW_SPACING // 2)
            column.pack_start(renderer, True)
            column.set_cell_data_func(renderer, self.__text_cell_data, column_index)
            self.append_column(column)
            self._tree_columns.append(column)

        self.set_model(Gtk.ListStore(*([object] * self._visible_columns)))

    def __text_cell_data(self, column, cell, model, iter_, column_index):
        row = model.get_value(iter_, column_index)
        cell.set_property("visible", row is not None)
        if row is None:
            cell.set_property("markup", "")
            cell.markup = ""
            return
        markup = row.get_markup()
        cell.set_property("markup", markup)
        cell.markup = markup

    def __populate_model(self) -> None:
        model = self.get_model()
        model.clear()

        if not self._rows:
            self.get_selection().unselect_all()
            return

        rows_per_column = (len(self._rows) + self._visible_columns - 1) // self._visible_columns
        grid = [[None for _ in range(self._visible_columns)] for _ in range(rows_per_column)]
        selected_position = None
        for index, row in enumerate(self._rows):
            row_index = index % rows_per_column
            column_index = index // rows_per_column
            grid[row_index][column_index] = row
            if row.key == self._selected_key:
                selected_position = (row_index, column_index)

        for grid_row in grid:
            model.append(grid_row)

        self.get_selection().unselect_all()
        if selected_position is not None:
            path = Gtk.TreePath((selected_position[0],))
            column = self._tree_columns[selected_position[1]]
            self.set_cursor(path, column, False)
        elif self._rows:
            self.set_cursor(Gtk.TreePath((0,)), self._tree_columns[0], False)

    def set_rows(self, rows: list[DrilldownRow], selected_key: str | None) -> None:
        self._rows = list(rows)
        self._selected_key = selected_key
        self._visible_columns = self.__column_count_for_width(self.get_allocated_width())
        self.__rebuild_columns()
        self.__populate_model()

    def get_selected_row(self) -> DrilldownRow | None:
        path, column = self.get_cursor()
        if path is None:
            return None
        column_index = self._tree_columns.index(column) if column in self._tree_columns else 0
        iter_ = self.get_model().get_iter(path)
        return self.get_model().get_value(iter_, column_index)

    def set_cursor_for_key(self, key: str) -> None:
        model = self.get_model()
        for row_index, grid_row in enumerate(model):
            for column_index in range(self._visible_columns):
                row = grid_row[column_index]
                if row is not None and row.key == key:
                    self.set_cursor(Gtk.TreePath((row_index,)),
                                    self._tree_columns[column_index], False)
                    return

    def activate_cursor(self) -> None:
        path, column = self.get_cursor()
        if path is not None and column is not None:
            self.row_activated(path, column)

    def get_row_labels(self) -> list[str]:
        return [row.label for row in self._rows]


class SequentialBrowser(Browser):
    name = _("Sequential Browser")
    accelerated_name = _("_Sequential Browser")
    keys = ["Sequential", "SequentialBrowser"]
    priority = 5

    def __init__(self, library):
        super().__init__(spacing=6, orientation=Gtk.Orientation.VERTICAL)

        self._library = library
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
        dsp_button = DspWindowOpener(self)
        search.pack_start(dsp_button, False, True, 0)
        self.pack_start(Align(search, left=6, right=6), False, True, 0)

        header = Gtk.Box(spacing=3, orientation=Gtk.Orientation.VERTICAL)
        breadcrumb_box = Gtk.Box(spacing=6, homogeneous=False)
        self._breadcrumb_buttons = {}
        for index, tag in enumerate(PATH_LEVELS):
            slot = Gtk.Box()
            button = CompactColorTouchButton(label=tag,
                                             color=CompactColorTouchButton.BLUE)
            button.set_size_request(200, 52)
            child = button.get_child()
            if isinstance(child, Gtk.Label):
                child.set_ellipsize(Pango.EllipsizeMode.END)
                child.set_single_line_mode(True)
                child.set_max_width_chars(24)
            button.connect("clicked", self.__breadcrumb_clicked, index)
            slot.pack_start(button, False, False, 0)
            breadcrumb_box.pack_start(slot, False, False, 0)
            self._breadcrumb_buttons[tag] = button
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
        self._query_filter = query.search if query.is_parsable else (lambda song: True)
        songs = list(filter(self._query_filter, self._library))
        bg = background_filter()
        if bg:
            songs = list(filter(bg, songs))
        return songs

    def __normalize_tag(self, tag: str) -> str:
        if tag in PEOPLE:
            return "artist"
        return tag

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
        return self.__normalize_tag(tag) in PATH_LEVELS

    def filter(self, tag, values):
        tag = self.__normalize_tag(tag)
        if tag not in PATH_LEVELS:
            return
        chosen = next(iter(values), None)
        level_index = PATH_LEVELS.index(tag)
        self._path_values[tag] = chosen
        self.__clear_deeper(level_index + 1)
        self._level_index = min(level_index + 1, len(LEVELS) - 1)
        self.activate()

    def list(self, tag):
        tag = self.__normalize_tag(tag)
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