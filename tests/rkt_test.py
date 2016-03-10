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
from __future__ import absolute_import

import uuid
import unittest
import xml.etree.ElementTree as ET

import convirt
import convirt.config
import convirt.rkt

from . import monkey
from . import testlib


class RktTests(testlib.RunnableTestCase):

    def test_created_not_running(self):
        rkt = convirt.rkt.Rkt(convirt.config.current())
        self.assertFalse(rkt.running)

    def test_runtime_name_none_before_start(self):
        rkt = convirt.rkt.Rkt(convirt.config.current())
        self.assertEqual(rkt.runtime_name(), None)

    def test_start_stop(self):
        rkt = convirt.rkt.Rkt(testlib.make_conf(run_dir=self.run_dir))
        root = ET.fromstring(testlib.minimal_dom_xml())
        rkt.configure(root)
        rkt.start()
        try:
            self.assertTrue(rkt.running)
        finally:
            rkt.stop()
            self.assertFalse(rkt.running)

    def test_start_twice(self):
        rkt = convirt.rkt.Rkt(testlib.make_conf(run_dir=self.run_dir))
        root = ET.fromstring(testlib.minimal_dom_xml())
        rkt.configure(root)
        rkt.start()
        try:
            self.assertRaises(convirt.runner.OperationFailed,
                              rkt.start)
        finally:
            # not part of the test, but we don't want
            # to pollute the environment
            rkt.stop()

    def test_start_twice(self):
        rkt = convirt.rkt.Rkt(testlib.make_conf(run_dir=self.run_dir))
        root = ET.fromstring(testlib.minimal_dom_xml())
        rkt.configure(root)
        rkt.start()
        try:
            self.assertRaises(convirt.runner.OperationFailed,
                              rkt.start)
        finally:
            # not part of the test, but we don't want
            # to pollute the environment
            rkt.stop()

    def test_stop_not_started(self):
        rkt = convirt.rkt.Rkt(testlib.make_conf(run_dir=self.run_dir))
        self.assertFalse(rkt.running)
        self.assertRaises(convirt.runner.OperationFailed, rkt.stop)

    def test_commandline_unquoted(self):
        rkt = convirt.rkt.Rkt(testlib.make_conf(run_dir=self.run_dir))
        root = ET.fromstring(testlib.minimal_dom_xml())
        rkt.configure(root)
        for arg in rkt.command_line():
            self.assertNotIn('"', arg)
