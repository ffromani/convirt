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

import os.path
import uuid
import unittest
import xml.etree.ElementTree as ET

import convirt
import convirt.config
import convirt.config.environ
import convirt.rkt

from . import monkey
from . import testlib


class RktTests(testlib.RunnableTestCase):

    def test_created_not_running(self):
        rkt = convirt.rkt.Rkt(convirt.config.environ.current())
        self.assertFalse(rkt.running)

    def test_runtime_name_none_before_start(self):
        rkt = convirt.rkt.Rkt(convirt.config.environ.current())
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



class NetworkTests(testlib.TestCase):

    def test_path(self):
        NAME = '99-test.conf'
        net = convirt.rkt.Network(name=NAME)
        self.assertTrue(net.path.endswith(NAME))
        self.assertTrue(net.path.startswith(convirt.rkt.Network.DIR))

    def test_save_without_changes(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                net = convirt.rkt.Network()
                net.save()
                self.assertFalse(os.path.exists(net.path))

    def test_save_forced(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                net = convirt.rkt.Network()
                net.save(force=True)
                self.assertTrue(os.path.exists(net.path))

    def test_update(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                net1 = convirt.rkt.Network()
                net1.update({
                    'bridge': 'foobar',
                    'subnet': '192.168.42.0',
                    'mask': 27,
                })
                net2 = convirt.rkt.Network()
                self.assertNotEquals(net1, net2)
                net1.save()
                self.assertTrue(os.path.exists(net1.path))

    def test_load(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                net1 = convirt.rkt.Network()
                net1.save(force=True)
                net2 = convirt.rkt.Network()
                net2.load()
                self.assertEquals(net1, net2)

    def test_clear(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                net = convirt.rkt.Network()
                net.save(force=True)
                self.assertTrue(os.path.exists(net.path))
                net.clear()
                self.assertFalse(os.path.exists(net.path))

    def test_context_manager(self):
        with testlib.named_temp_dir() as tmp_dir:
            with monkey.patch_scope([(convirt.rkt.Network, 'DIR', tmp_dir)]):
                conf1 = {
                    'name': 'test-net',
                    'bridge': 'foobar',
                    'subnet': '192.168.42.0',
                    'mask': 27,
                }
                conf2 = conf1.copy()
                conf2['mask'] = 28

                net1 = convirt.rkt.Network()
                net1.update(conf1)
                net1.save()
                self.assertEquals(net1.get_conf(), conf1)

                with convirt.rkt.Network() as net2:
                    net2.update(conf2)

                net1.load()
                self.assertEquals(net1.get_conf(), conf2)
