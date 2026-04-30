from gi.repository import Gtk
from senf import fsnative

from tests import TestCase, run_gtk_loop
from .helper import visible

from quodlibet import config
from quodlibet.browsers.sequential.main import SequentialBrowser, UNKNOWN_VALUE
from quodlibet.formats import AudioFile
from quodlibet.library import SongLibrary, SongLibrarian
from quodlibet.browsers.sequential.main import DrilldownRow


SONGS = [
    AudioFile({
        "title": "Alpha Song",
        "artist": "Artist A",
        "album": "Album A1",
        "genre": "Rock",
        "~filename": fsnative("/tmp/alpha-song"),
    }),
    AudioFile({
        "title": "Beta Song",
        "artist": "Artist A",
        "album": "Album A2 With A Very Long Name",
        "genre": "Rock",
        "~filename": fsnative("/tmp/beta-song"),
    }),
    AudioFile({
        "title": "Gamma Song",
        "artist": "Artist B",
        "album": "Album B1",
        "genre": "Jazz",
        "~filename": fsnative("/tmp/gamma-song"),
    }),
    AudioFile({
        "title": "Delta Song",
        "album": "Album Unknown",
        "genre": "Rock",
        "~filename": fsnative("/tmp/delta-song"),
    }),
]


class TSequentialBrowser(TestCase):
    def _breadcrumb_box(self):
        return self.bar._breadcrumb_buttons["genre"].get_parent().get_parent()

    def _breadcrumb_order(self):
        return [
            tag for slot in self._breadcrumb_box().get_children()
            for tag, button in self.bar._breadcrumb_buttons.items()
            if button.get_parent() is slot
        ]

    def setUp(self):
        config.init()
        library = SongLibrary()
        library.librarian = SongLibrarian()
        for song in SONGS:
            song.sanitize()
        library.add(SONGS)
        SequentialBrowser.init(library)
        self.bar = SequentialBrowser(library)
        self.container = self.bar.pack(Gtk.Label())

        self.last = None

        def selected_cb(browser, songs, *args):
            self.last = list(songs)

        self.bar.connect("songs-selected", selected_cb)

    def tearDown(self):
        self.bar.unpack(self.container, self.bar._songpane)
        self.bar.destroy()
        config.quit()

    def test_starts_on_genres(self):
        with visible(self.container):
            self.bar.activate()
            self.assertEqual(self._breadcrumb_order(), ["genre", "artist", "album"])
            self.assertFalse(self._breadcrumb_box().get_homogeneous())
            self.assertEqual(self.bar._view.get_row_labels(), ["Jazz", "Rock"])
            self.assertEqual(self.bar._stack.get_visible_child_name(), "browser")

    def test_selection_does_not_advance_until_click(self):
        with visible(self.container):
            self.bar.activate()
            self.bar._view.set_cursor_for_key("Rock")
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_buttons["genre"].get_label(), "genre")
            self.assertEqual(self.bar._breadcrumb_buttons["artist"].get_label(), "artist")
            self.assertEqual(self.bar._breadcrumb_buttons["album"].get_label(), "album")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "")
            self.assertFalse(self.bar._breadcrumb_buttons["genre"].get_visible())
            self.assertFalse(self.bar._breadcrumb_buttons["artist"].get_visible())
            self.assertFalse(self.bar._breadcrumb_buttons["album"].get_visible())
            self.assertFalse(self.bar._breadcrumb_buttons["genre"].get_sensitive())

    def test_single_click_advances(self):
        with visible(self.container):
            self.bar.activate()
            self.bar._view.set_cursor_for_key("Rock")
            self.bar._view.activate_cursor()
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_buttons["genre"].get_label(), "genre")
            self.assertEqual(self.bar._breadcrumb_buttons["artist"].get_label(), "artist")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock")
            self.assertTrue(self.bar._breadcrumb_buttons["genre"].get_visible())
            self.assertFalse(self.bar._breadcrumb_buttons["artist"].get_visible())
            self.assertTrue(self.bar._breadcrumb_buttons["genre"].get_sensitive())
            self.assertFalse(self.bar._breadcrumb_buttons["artist"].get_sensitive())
            self.assertEqual(self.bar._view.get_row_labels(), ["Artist A", "Unknown"])

    def test_back_returns_to_previous_level(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock")
            self.bar._breadcrumb_buttons["genre"].clicked()
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "")

    def test_artist_breadcrumb_returns_to_artist_list(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            self.bar.filter("artist", ["Artist A"])
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A")
            self.assertTrue(self.bar._breadcrumb_buttons["genre"].get_visible())
            self.assertTrue(self.bar._breadcrumb_buttons["artist"].get_visible())
            self.assertFalse(self.bar._breadcrumb_buttons["album"].get_visible())
            self.bar._breadcrumb_buttons["artist"].clicked()
            run_gtk_loop()
            self.assertEqual(self.bar._view.get_row_labels(), ["Artist A", "Unknown"])
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock")

    def test_album_breadcrumb_returns_to_album_list(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            self.bar.filter("artist", ["Artist A"])
            self.bar.filter("album", ["Album A1"])
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A / Album A1")
            self.assertTrue(self.bar._breadcrumb_buttons["album"].get_visible())
            self.bar._breadcrumb_buttons["album"].clicked()
            run_gtk_loop()
            self.assertEqual(self.bar._view.get_row_labels(), ["Album A1", "Album A2 With A Very Long Name"])
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A")

    def test_album_activation_shows_song_page(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            self.bar.filter("artist", ["Artist A"])
            self.bar.filter("album", ["Album A1"])
            run_gtk_loop()
            self.assertEqual(self.last, [SONGS[0]])
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A / Album A1")

    def test_filter_text_limits_visible_rows(self):
        with visible(self.container):
            self.bar.filter_text("genre=Jazz")
            run_gtk_loop()
            self.assertEqual(self.bar._view.get_row_labels(), ["Jazz"])

    def test_unknown_artist_is_available(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            run_gtk_loop()
            self.assertEqual(self.bar._view.get_row_labels(), ["Artist A", "Unknown"])
            self.bar.filter("artist", [UNKNOWN_VALUE])
            run_gtk_loop()
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Unknown")
            self.assertEqual(self.bar._view.get_row_labels(), ["Album Unknown"])

    def test_restore_rebuilds_path(self):
        self.bar.filter("genre", ["Rock"])
        self.bar.filter("artist", ["Artist A"])
        self.bar.save()
        self.bar.unfilter()
        self.bar.restore()
        self.bar.activate()
        self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A")

    def test_multi_column_layout_fills_across_first(self):
        rows = [
            DrilldownRow.create(f"genre-{index}", f"Genre {index}", 1)
            for index in range(6)
        ]
        self.bar._view._visible_columns = 2
        self.bar._view._rows = rows
        self.bar._view._selected_key = None
        self.bar._view._DrilldownView__rebuild_columns()
        self.bar._view._DrilldownView__populate_model()

        model = self.bar._view.get_model()
        self.assertEqual(len(self.bar._view.get_columns()), 2)
        self.assertEqual(model[0][0].label, "Genre 0")
        self.assertEqual(model[0][1].label, "Genre 1")
        self.assertEqual(model[1][0].label, "Genre 2")
        self.assertEqual(model[1][1].label, "Genre 3")
        self.assertEqual(model[2][0].label, "Genre 4")
        self.assertEqual(model[2][1].label, "Genre 5")

    def test_row_markup_truncates_to_forty_characters_without_counts(self):
        row = DrilldownRow.create(
            "album-1",
            "123456789012345678901234567890123456789012345",
            1,
        )
        self.assertEqual(row.get_markup(), "123456789012345678901234567890123456789…")