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

import subprocess
import uuid

import convirt
import convirt.command
import convirt.runner

from . import monkey
from . import testlib


class RuntimeListTests(testlib.TestCase):

    def test_pristine(self):
        runr = convirt.runner.Subproc('testing')
        conts = list(runr.get_all())
        self.assertEqual(conts, [])

    # we need something we are confident can't exist
    @monkey.patch_function(convirt.runner, 'PREFIX', str(uuid.uuid4()))
    def test_no_output(self):
        runr = convirt.runner.Subproc('testing')
        conts = list(runr.get_all())
        self.assertEqual(conts, [])

    # TODO: add test with fake correct output
    def test_single_service(self):
        VM_UUID = 'd7a0005e-ee05-4e61-9fbe-d2e93d59327c'

        def fake_check_output(*args):
            return """
convirt-%s.service                                                loaded active running   /bin/sleep 10m
""" % VM_UUID

        with monkey.patch_scope([(subprocess, 'check_output',
                                  fake_check_output)]):
            runr = convirt.runner.Subproc('testing')
            conts = list(runr.get_all())
            self.assertEqual(conts, [VM_UUID])

    def test__parse_systemctl_one_service(self):
        output = """
foobar.service                                                                                      loaded active running   /bin/sleep 10m
"""
        names = list(convirt.runner._parse_systemctl_list_units(output))
        self.assertEqual(names, ["foobar"])

    def test__parse_systemctl_empty_output(self):
        output = ""
        names = list(convirt.runner._parse_systemctl_list_units(output))
        self.assertEqual(names, [])

    def test__parse_systemctl_corrupted_output(self):
        output = """
foobar.service    somehow messed
"""
        names = list(convirt.runner._parse_systemctl_list_units(output))
        self.assertEqual(names, [])

    def test__parse_systemctl_no_services(self):
        output = """
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
        names = list(convirt.runner._parse_systemctl_list_units(output))
        self.assertEqual(names, [])


class SubprocTests(testlib.TestCase):

    def setUp(self):
        self.unit_name = 'test'

    def test_created_not_running(self):
        runner = convirt.runner.Subproc(self.unit_name)
        self.assertFalse(runner.running)

    def test_run_default_conf(self):

        def _fake_call(cmd):
            # at least:
            # 1. systemd-run
            # 2. --unit
            # 3. exec path
            self.assertGreaterEqual(len(cmd), 3)
            self.assertIn('systemd-run', cmd[0])
            unit_found = any(
                c.startswith('--unit') and self.unit_name in c
                for c in cmd
            )
            self.assertTrue(unit_found)

        runner = convirt.runner.Subproc(self.unit_name)
        with monkey.patch_scope([(runner, '_call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])
            self.assertTrue(runner.running)

    def test_run_with_specific_uid(self):
        uid = 1764

        def _fake_call(cmd):
            uid_found = any(
                'uid=%i' % uid in c for c in cmd
            )
            self.assertTrue(uid_found)

        conf = convirt.config.environ.current()
        conf.uid = uid
        runner = convirt.runner.Subproc(self.unit_name)
        runner.configure(conf)
        with monkey.patch_scope([(runner, '_call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])

    def test_run_with_specific_gid(self):
        gid = 1764

        def _fake_call(cmd):
            gid_found = any(
                'gid=%i' % gid in c for c in cmd
            )
            self.assertTrue(gid_found)

        conf = convirt.config.environ.current()
        conf.gid = gid
        runner = convirt.runner.Subproc(self.unit_name)
        runner.configure(conf)
        with monkey.patch_scope([(runner, '_call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])

    def test_call_fails(self):
        conf = convirt.config.environ.current()
        conf.use_sudo = True
        runner = convirt.runner.Subproc(self.unit_name)
        runner.configure(conf)
        _false = convirt.command.Path('false')
        with monkey.patch_scope([(convirt.runner, '_SUDO', _false)]):
            self.assertRaises(
                convirt.runner.OperationFailed,
                runner.start,
                ['/bin/sleep', '42s'],
            )

    def test_stop(self):

        def _fake_call(cmd):
            # exactly:
            # 1. systemdctl
            # 2. stop
            # 3. unit-name
            self.assertEqual(len(cmd), 3)
            self.assertIn('systemctl', cmd[0])
            self.assertEqual('stop', cmd[1])
            self.assertIn(self.unit_name, cmd[2])

        runner = convirt.runner.Subproc(self.unit_name)
        with monkey.patch_scope([(runner, '_call', _fake_call)]):
            runner.stop()

    def test_stats_pristine(self):
        stats = list(convirt.runner.Subproc.stats())
        self.assertEqual(stats, [])
