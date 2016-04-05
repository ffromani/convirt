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

import convirt.config
import convirt.config.environ

from . import testlib


class ConfigTestsMixin(object):

    def setUp(self):
        self.saved_conf = self.CONFIG_MODULE.current()

    def tearDown(self):
        self.CONFIG_MODULE.setup(self.saved_conf)

    def test_default_not_empty(self):
        conf = self.CONFIG_MODULE.current()
        self.assertTrue(conf)
        self.assertGreaterEqual(len(conf), 0)

    def test_get(self):
        self.assertNotRaises(self.CONFIG_MODULE.current)

    def test_repr(self):
        self.assertTrue(repr(self.CONFIG_MODULE.current()))


class EnvironTests(ConfigTestsMixin, testlib.TestCase):

    CONFIG_MODULE = convirt.config.environ

    def test_setup_new(self):
        conf = convirt.config.environ.Environment(
            uid=42,
            gid=42,
            tools_dir='/usr/local/libexec/convirt/test',
            run_dir='/run/convirt_d',
            use_sudo=False,
            cgroup_slice='convirt_slice',
            cleanup_expire_period=1000,
            cleanup_grace_period=10,
        )
        self.assertNotRaises(convirt.config.environ.setup, conf)
        self.assertEquals(convirt.config.environ.current(), conf)
        self.assertFalse(convirt.config.environ.current() is conf)

    def test_setup(self):
        conf = convirt.config.environ.current()
        conf.run_dir = '/run/convirt/random/dir'
        convirt.config.environ.setup(conf)
        self.assertEquals(convirt.config.environ.current(), conf)
        self.assertFalse(convirt.config.environ.current() is conf)

    def test_update(self):
        conf = convirt.config.environ.update(
            run_dir='/run/convirt/another/random/dir')
        self.assertEquals(convirt.config.environ.current(), conf)
        self.assertFalse(convirt.config.environ.current() is conf)

    def test_attribute_does_not_disappear(self):
        conf = convirt.config.environ.current()
        ref_value = conf.use_sudo
        del conf['use_sudo']
        convirt.config.environ.setup(conf)
        new_conf = convirt.config.environ.current()
        self.assertEquals(new_conf.use_sudo, ref_value)


class NetworkTests(ConfigTestsMixin, testlib.TestCase):

    CONFIG_MODULE = convirt.config.network

    def test_setup_new(self):
        conf = convirt.config.network.Network(
            name='convirt-net',
            bridge='convirt-bridge',
            subnet='192.168.192.0',
            mask=24,
        )
        self.assertNotRaises(convirt.config.network.setup, conf)
        self.assertEquals(convirt.config.network.current(), conf)
        self.assertFalse(convirt.config.network.current() is conf)

    def test_setup(self):
        conf = convirt.config.network.current()
        conf.bridge = 'convirt-br'
        convirt.config.network.setup(conf)
        self.assertEquals(convirt.config.network.current(), conf)
        self.assertFalse(convirt.config.network.current() is conf)

    def test_update(self):
        conf = convirt.config.network.update(name='convnet')
        self.assertEquals(convirt.config.network.current(), conf)
        self.assertFalse(convirt.config.network.current() is conf)

    def test_attribute_does_not_disappear(self):
        conf = convirt.config.network.current()
        ref_value = conf.subnet
        del conf['subnet']
        convirt.config.network.setup(conf)
        new_conf = convirt.config.network.current()
        self.assertEquals(new_conf.subnet, ref_value)
