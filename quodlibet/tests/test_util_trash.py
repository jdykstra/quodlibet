# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

"""Tests for quodlibet.util.trash."""

import os
import sys

from quodlibet.util import is_windows
from tests import TestCase, skipIf, mkstemp

from quodlibet import config
from quodlibet.util.trash import use_trash, trash


class Ttrash(TestCase):

    def setUp(self):
        config.init()

    def tearDown(self):
        config.quit()

    def test_use_trash_is_false_on_non_posix(self):
        old_os_name = os.name
        try:
            os.name = 'not posix'
            self.assertFalse(use_trash())
        finally:
            os.name = old_os_name

    def test_use_trash_is_false_on_darwin(self):
        old_os_name = os.name
        old_sys_platform = sys.platform
        try:
            os.name = 'posix'
            sys.platform = 'darwin'
            self.assertFalse(use_trash())
        finally:
            os.name = old_os_name
            sys.platform = old_sys_platform

    def test_use_trash_is_true_by_default_on_posix(self):
        old_os_name = os.name
        old_sys_platform = sys.platform
        try:
            os.name = 'posix'
            sys.platform = 'linux'
            self.assertTrue(use_trash())
        finally:
            os.name = old_os_name
            sys.platform = old_sys_platform

    def test_use_trash_is_false_when_bypassed(self):
        old_os_name = os.name
        old_sys_platform = sys.platform
        try:
            config.set('settings', 'bypass_trash', "true")
            os.name = 'posix'
            sys.platform = 'linux'
            self.assertFalse(use_trash())
        finally:
            os.name = old_os_name
            sys.platform = old_sys_platform

    @skipIf(is_windows(), reason="Trash not supported on Windows")
    def test_trash_removes_file(self):
        filename = mkstemp()[1]
        with open(filename, "w") as f:
            f.write("\n")
        self.failUnless(os.path.exists(filename))
        trash(filename)
        self.failIf(os.path.exists(filename))
