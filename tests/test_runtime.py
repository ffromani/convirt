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

import errno
import os
import subprocess
import uuid
import unittest

import convirt
import convirt.command
import convirt.runtime

from . import monkey
from . import testlib


class RuntimeListTests(testlib.TestCase):

    def test_pristine(self):
        conts = list(convirt.runtime.get_all())
        self.assertEqual(conts, [])

    # we need something we are confident can't exist
    @monkey.patch_function(convirt.runtime, '_PREFIX', str(uuid.uuid4()))
    def test_no_output(self):
        conts = list(convirt.runtime.get_all())
        self.assertEqual(conts, [])

    # TODO: add test with fake correct output
    def test_single_service(self):
        VM_UUID = 'd7a0005e-ee05-4e61-9fbe-d2e93d59327c'

        def fake_check_output(*args):
            return \
"""
convirt-%s.service                                                loaded active running   /bin/sleep 10m
""" % VM_UUID

        with monkey.patch_scope([(subprocess, 'check_output',
                                  fake_check_output)]):
            conts = list(convirt.runtime.get_all())
            self.assertEqual(conts, [VM_UUID])


    def test__parse_systemctl_one_service(self):
        output = \
"""
foobar.service                                                                                      loaded active running   /bin/sleep 10m
"""
        names = list(convirt.runtime._parse_systemctl_list_units(output))
        self.assertEqual(names, ["foobar"])

    def test__parse_systemctl_empty_output(self):
        output = \
"""
"""
        names = list(convirt.runtime._parse_systemctl_list_units(output))
        self.assertEqual(names, [])

    def test__parse_systemctl_no_services(self):
        output = \
"""
proc-sys-fs-binfmt_misc.automount                                                                   loaded active waiting   Arbitrary Executable File Formats File System Automount Point
sys-module-fuse.device                                                                              loaded active plugged   /sys/module/fuse
sys-subsystem-net-devices-virbr0.device                                                             loaded active plugged   /sys/subsystem/net/devices/virbr0
dev-hugepages.mount                                                                                 loaded active mounted   Huge Pages File System
cups.path                                                                                           loaded active waiting   CUPS Scheduler
session-1.scope                                                                                     loaded active running   Session 1 of user foobar
-.slice                                                                                             loaded active active    Root Slice
cups.socket                                                                                         loaded active running   CUPS Scheduler
swap.target                                                                                         loaded active active    Swap
systemd-tmpfiles-clean.timer                                                                        loaded active waiting   Daily Cleanup of Temporary Directories
"""
        names = list(convirt.runtime._parse_systemctl_list_units(output))
        self.assertEqual(names, [])


class TruePath(object):
    def cmd(self):
        return True


class NonePath(object):
    def cmd(self):
        return None


class RaisingPath(object):
    def cmd(self):
        raise convirt.command.NotFound()


class RuntimeBaseAvailableTests(testlib.TestCase):

    def test_raising(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH', RaisingPath())]):
            self.assertFalse(convirt.runtime.Base.available())

    def test_not_available(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH', NonePath())]):
            self.assertFalse(convirt.runtime.Base.available())

    def test_available(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH', TruePath())]):
            self.assertTrue(convirt.runtime.Base.available())


class RuntimeBaseAPITests(testlib.TestCase):

    def setUp(self):
        self.base = convirt.runtime.Base(str(uuid.uuid4()), '/tmp')

    def test_configure(self):
        self.assertRaises(NotImplementedError, self.base.configure, '')

    def test_start(self):
        self.assertRaises(NotImplementedError, self.base.start)


class RuntimeBaseFacilitiesTests(testlib.TestCase):

    def setUp(self):
        self.vm_uuid = str(uuid.uuid4())
        self.base = convirt.runtime.Base(self.vm_uuid, '/tmp')

    def test_run(self):

        def _fake_exec(cmd):
            # at least:
            # 1. systemd-run
            # 2. --unit
            # 3. exec path
            self.assertGreaterEqual(len(cmd), 3)
            self.assertIn('systemd-run', cmd[0])
            unit_found = any(
                c.startswith('--unit') and self.vm_uuid in c
                for c in cmd
            )
            self.assertTrue(unit_found)

        with monkey.patch_scope([(self.base, '_exec', _fake_exec)]):
            self.base.run(['/bin/sleep', '42m'])

    def test_stop(self):

        def _fake_exec(cmd):
            # exactly:
            # 1. systemdctl
            # 2. stop
            # 3. unit-name
            self.assertEqual(len(cmd), 3)
            self.assertIn('systemctl', cmd[0])
            self.assertEqual('stop', cmd[1])
            self.assertIn(self.vm_uuid, cmd[2])

        with monkey.patch_scope([(self.base, '_exec', _fake_exec)]):
            self.base.stop()

    def test_stats_pristine(self):
        stats = list(convirt.runtime.Base.stats())
        self.assertEqual(stats, [])

    def test_stats_faked_no_conts(self):
        with monkey.patch_scope([(subprocess, 'check_output',
                                  _fake_check_output_sd_cgtop_sys)]):
            stats = list(convirt.runtime.Base.stats())
            self.assertEqual(stats, [])

    def test_stats_faked__conts(self):
        with monkey.patch_scope([(subprocess, 'check_output',
                                  _fake_check_output_sd_cgtop_conts)]):
            stats = list(convirt.runtime.Base.stats())
            self.assertEqual(len(stats), len(_SD_CGTOP_CONTS))
            for vm_uuid in _SD_CGTOP_CONTS:
                for stat in stats:
                    self.assertIn(vm_uuid, stat.path)


def _fake_check_output_sd_cgtop_sys(cmd):
    return _SD_CGTOP_SYS


def _fake_check_output_sd_cgtop_conts(cmd):
    return \
"""
/                                                                   269      -     1.6G        -        -
""" + ''.join(_SD_CGTOP_CONTS.values())


_SD_CGTOP_SYS = \
"""
/                                                 269      -     1.6G        -        -
/system.slice/accounts-daemon.service               1      -        -        -        -
/system.slice/atd.service                           1      -        -        -        -
/system.slice/auditd.service                        3      -        -        -        -
/system.slice/chronyd.service                       1      -        -        -        -
/system.slice/crond.service                         1      -        -        -        -
/system.slice/cups.service                          1      -        -        -        -
/system.slice/libvirtd.service                      3      -        -        -        -
/system.slice/lvm2-lvmetad.service                  1      -        -        -        -
/system.slice/systemd-journald.service              1      -        -        -        -
/system.slice/systemd-logind.service                1      -        -        -        -
/system.slice/systemd-udevd.service                 1      -        -        -        -
/user.slice/user-1000.slice/session-1.scope        63      -        -        -        -
/user.slice/user-1000.slice/user@1000.service       2      -        -        -        -
/user.slice/user-42.slice/session-c1.scope         25      -        -        -        -
/user.slice/user-42.slice/user@42.service           2      -        -        -        -
"""


_SD_CGTOP_CONTS = {
    "823b2654-3e9c-4e6f-834d-31c492b9ae92": 
"""
/system.slice/convirt-823b2654-3e9c-4e6f-834d-31c492b9ae92.service    1      -        -        -        -
""",
}
