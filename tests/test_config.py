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

import convirt.config

from . import testlib


class ConfigTests(testlib.TestCase):

    def setUp(self):
        self.saved_conf = convirt.config.current()

    def tearDown(self):
        convirt.config.setup(self.saved_conf)

    def test_default_not_empty(self):
        conf = convirt.config.current()
        self.assertTrue(conf)
        self.assertGreaterEqual(len(conf), 0)

    def test_get(self):
        self.assertNotRaises(convirt.config.current)

    def test_update(self):
        conf = convirt.config.Environment(
            uid=42,
            gid=42,
            tools_dir='/usr/local/libexec/convirt/test',
            run_dir='/run/convirt_d',
            use_sudo=False,
            cgroup_slice='convirt_slice',
        )
        self.assertNotRaises(convirt.config.setup, conf)
        self.assertEquals(convirt.config.current(), conf)
        self.assertFalse(convirt.config.current() is conf)

    def test_mutate(self):
        conf = convirt.config.current()
        conf.run_dir = '/run/convirt/random/dir'
        convirt.config.setup(conf)
        self.assertEquals(convirt.config.current(), conf)
        self.assertFalse(convirt.config.current() is conf)

    def test_attribute_does_not_disappear(self):
        conf = convirt.config.current()
        ref_value = conf.use_sudo
        del conf['use_sudo']
        convirt.config.setup(conf)
        new_conf = convirt.config.current()
        self.assertEquals(new_conf.use_sudo, ref_value)
