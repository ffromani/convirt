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
