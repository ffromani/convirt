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

import convirt.metrics.cgroups

from . import monkey
from . import testlib


class CgroupTests(testlib.CgroupTestCase):

    def test_empty_cgroups(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        self.assertEquals(mon.cgroups, ())
    
    def test_empty_cpuacct(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        self.assertIs(mon.cpuacct, None)
    
    def test_empty_memory(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        self.assertIs(mon.memory, None)

    def test_empty_blkio(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        self.assertIs(mon.blkio, None)

    def test_from_pid(self):
        mon = convirt.metrics.cgroups.Monitorable.from_pid(self.pid)
        self.assertTrue(mon.cgroups)

    def test_pid_matches(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        self.assertEquals(mon.pid, self.pid)
    
    def test_setup(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        mon.setup()
        self.assertTrue(mon.cgroups)

    def test_cgroups_found(self):
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        mon.setup()
        for cg in ('memory', 'cpuacct', 'blkio'):
            self.assertIn(cg, mon.cgroups)

    def test_update_without_setup(self):        
        mon = convirt.metrics.cgroups.Monitorable(self.pid)
        mon.update()
        self.assertEquals(mon.cgroups, ())
