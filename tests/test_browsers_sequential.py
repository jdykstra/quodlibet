from gi.repository import Gtk
from senf import fsnative

from tests import TestCase, run_gtk_loop
from .helper import visible

from quodlibet import config
from quodlibet.browsers.sequential.main import SequentialBrowser, UNKNOWN_VALUE
from quodlibet.formats import AudioFile
from quodlibet.library import SongLibrary, SongLibrarian


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
            self.assertEqual(self.bar._title_label.get_text(), "Genres")
            self.assertEqual(self.bar._view.get_row_labels(), ["Jazz", "Rock"])
            self.assertEqual(self.bar._stack.get_visible_child_name(), "browser")

    def test_selection_does_not_advance(self):
        with visible(self.container):
            self.bar.activate()
            self.bar._view.set_cursor(Gtk.TreePath((1,)))
            run_gtk_loop()
            self.assertEqual(self.bar._title_label.get_text(), "Genres")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "")

    def test_row_activation_advances(self):
        with visible(self.container):
            self.bar.activate()
            self.bar._view.set_cursor(Gtk.TreePath((1,)))
            self.bar._view.row_activated(Gtk.TreePath((1,)), self.bar._view.get_column(0))
            run_gtk_loop()
            self.assertEqual(self.bar._title_label.get_text(), "Artists")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock")
            self.assertEqual(self.bar._view.get_row_labels(), ["Artist A", "Unknown"])

    def test_back_returns_to_previous_level(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            run_gtk_loop()
            self.assertEqual(self.bar._title_label.get_text(), "Artists")
            self.bar._back_button.clicked()
            run_gtk_loop()
            self.assertEqual(self.bar._title_label.get_text(), "Genres")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "")

    def test_album_activation_shows_song_page(self):
        with visible(self.container):
            self.bar.filter("genre", ["Rock"])
            self.bar.filter("artist", ["Artist A"])
            self.bar.filter("album", ["Album A1"])
            run_gtk_loop()
            self.assertEqual(self.last, [SONGS[0]])
            self.assertEqual(self.bar._title_label.get_text(), "Songs")

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
            self.assertEqual(self.bar._title_label.get_text(), "Albums")
            self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Unknown")
            self.assertEqual(self.bar._view.get_row_labels(), ["Album Unknown"])

    def test_restore_rebuilds_path(self):
        self.bar.filter("genre", ["Rock"])
        self.bar.filter("artist", ["Artist A"])
        self.bar.save()
        self.bar.unfilter()
        self.bar.restore()
        self.bar.activate()
        self.assertEqual(self.bar._title_label.get_text(), "Albums")
        self.assertEqual(self.bar._breadcrumb_label.get_text(), "Rock / Artist A")