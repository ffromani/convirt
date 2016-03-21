from __future__ import absolute_import
#
# Copyright 2015-2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#


import unittest

import convirt
import convirt.api
import convirt.runtime

from . import monkey
from . import testlib


class FunctionsTests(testlib.TestCase):

    def setUp(self):
        convirt.api.clear()

    def test_no_runtimes_supported(self):
        with monkey.patch_scope([(convirt.rkt.Rkt, '_PATH',
                                  testlib.NonePath())]):
            self.assertFalse(convirt.api.supported())

    def test_supported(self):
        with monkey.patch_scope([(convirt.rkt.Rkt, '_PATH',
                                  testlib.TruePath())]):
            self.assertTrue(convirt.api.supported())

    def test_create_unsupported(self):
        self.assertRaises(convirt.runtime.Unsupported,
                          convirt.api.create,
                          'docker')

    def test_setup_runtime(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.setup()
        self.assertTrue(FakeRuntime.setup_runtime_done)

    def test_setup_runtime_register(self):
        def _find_runtimes():  # FIXME: ugly
            return {
                FakeRuntime.NAME: FakeRuntime
            }
        with monkey.patch_scope(
                [(convirt.api, '_find_runtimes', _find_runtimes)]
            ):
            convirt.api.setup(register=True)
        self.assertTrue(FakeRuntime.setup_runtime_done)
        self.assertEquals(convirt.api.supported(),
                          frozenset([FakeRuntime.NAME]))

    def test_setup_runtime_twice(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.setup()
        self.assertRaises(convirt.api.APIError,
                          convirt.api.setup)

    def test_teardown_runtime(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.setup()
        convirt.api.teardown()
        self.assertTrue(FakeRuntime.teardown_runtime_done)

    def test_teardown_runtime_twice(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.setup()
        convirt.api.teardown()
        self.assertRaises(convirt.api.APIError,
                          convirt.api.teardown)

    def test_teardown_runtime_clear(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.setup(register=False)
        convirt.api.teardown(clear=True)
        self.assertTrue(FakeRuntime.teardown_runtime_done)
        self.assertEquals(convirt.api.supported(), frozenset())

    def test_configure_runtime(self):
        convirt.api._runtimes[FakeRuntime.NAME] = FakeRuntime
        convirt.api.configure()
        self.assertTrue(FakeRuntime.configure_runtime_done)


class FakeRuntime(object):

    setup_runtime_done = False

    teardown_runtime_done = False

    configure_runtime_done = False

    NAME = 'FAKE'

    @classmethod
    def setup_runtime(cls):
        cls.setup_runtime_done = True

    @classmethod
    def teardown_runtime(cls):
        cls.teardown_runtime_done = True

    @classmethod
    def configure_runtime(cls):
        cls.configure_runtime_done = True
