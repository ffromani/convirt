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
import xml.etree.ElementTree as ET

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


class RaisingPath(object):
    def cmd(self):
        raise convirt.command.NotFound()


class RuntimeBaseAvailableTests(testlib.TestCase):

    def test_raising(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH', RaisingPath())]):
            self.assertFalse(convirt.runtime.Base.available())

    def test_not_available(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH',
                                  testlib.NonePath())]):
            self.assertFalse(convirt.runtime.Base.available())

    def test_available(self):
        with monkey.patch_scope([(convirt.runtime.Base, '_PATH',
                                  testlib.TruePath())]):
            self.assertTrue(convirt.runtime.Base.available())


class RuntimeBaseTests(testlib.TestCase):

    def setUp(self):
        self.vm_uuid = str(uuid.uuid4())
        self.base = convirt.runtime.Base(self.vm_uuid)

    def test_unit_name(self):
        self.assertIn(self.vm_uuid, self.base.unit_name())

    def test_setup(self):
        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            base = convirt.runtime.Base(self.vm_uuid, conf)

            base.setup()
            # XXX
            self.assertTrue(os.path.isdir(base._run_dir))
            self.assertNotEquals(base._run_dir, conf.run_dir)
            self.assertTrue(base._run_dir.startswith(conf.run_dir))

    def test_teardown(self):
        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            base = convirt.runtime.Base(self.vm_uuid, conf)
            base.setup()
            base.teardown()
            self.assertFalse(os.path.exists(base._run_dir))


class RuntimeBaseAPITests(testlib.TestCase):

    def setUp(self):
        self.base = convirt.runtime.Base(str(uuid.uuid4()))

    def test_start(self):
        self.assertRaises(NotImplementedError, self.base.start, '')

    def test_stop(self):
        self.assertRaises(NotImplementedError, self.base.stop)

    def test_status(self):
        self.assertRaises(NotImplementedError, self.base.status)

    def test_runtime_name(self):
        self.assertRaises(NotImplementedError, self.base.runtime_name)


class RunnerTests(testlib.TestCase):

    def setUp(self):
        self.unit_name = 'test'

    def test_created_not_running(self):
        runner = convirt.runtime.Runner(self.unit_name)
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

        runner = convirt.runtime.Runner(self.unit_name)
        with monkey.patch_scope([(runner, 'call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])
            self.assertTrue(runner.running)

    def test_run_with_specific_uid(self):
        uid = 1764

        def _fake_call(cmd):
            uid_found = any(
                'uid=%i' % uid in c for c in cmd
            )
            self.assertTrue(uid_found)

        conf = convirt.config.current()
        conf.uid = uid
        runner = convirt.runtime.Runner(self.unit_name, conf)
        with monkey.patch_scope([(runner, 'call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])

    def test_run_with_specific_gid(self):
        gid = 1764

        def _fake_call(cmd):
            gid_found = any(
                'gid=%i' % gid in c for c in cmd
            )
            self.assertTrue(gid_found)

        conf = convirt.config.current()
        conf.gid = gid
        runner = convirt.runtime.Runner(self.unit_name, conf)
        with monkey.patch_scope([(runner, 'call', _fake_call)]):
            runner.start(['/bin/sleep', '42m'])


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

        runner = convirt.runtime.Runner(self.unit_name)
        with monkey.patch_scope([(runner, 'call', _fake_call)]):
            runner.stop()

    def test_stats_pristine(self):
        stats = list(convirt.runtime.Runner.stats())
        self.assertEqual(stats, [])


class RuntimeBaseConfigureTests(testlib.TestCase):

    def setUp(self):
        self.vm_uuid = str(uuid.uuid4())
        self.base = convirt.runtime.Base(self.vm_uuid)

    def test_missing_content(self):
        root = ET.fromstring(
        """<domain type='kvm' id='2'>
        </domain>""")
        self.assertRaises(convirt.runtime.ConfigError,
                          self.base.configure,
                          root)

    def test_missing_memory(self):
        root = ET.fromstring(
        """<domain type='kvm' id='2'>
          <devices>
            <disk type='file' device='disk' snapshot='no'>
              <driver name='qemu' type='raw' cache='none' error_policy='stop' io='threads'/>
              <source file='/random/path/to/disk/image'>
                <seclabel model='selinux' labelskip='yes'/>
              </source>
              <backingStore/>
              <target dev='vdb' bus='virtio'/>
              <serial>90bece76-2df6-4a88-bfc8-f6f7461b7b8b</serial>
              <alias name='virtio-disk1'/>
              <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
            </disk>
          </devices>
        </domain>""")
        self.assertRaises(convirt.runtime.ConfigError,
                          self.base.configure,
                          root)

    def test_missing_disk(self):
        root = ET.fromstring(
        """<domain type='kvm' id='2'>
          <maxMemory slots='16' unit='KiB'>4294967296</maxMemory>
          <devices>
          </devices>
        </domain>""")
        self.assertRaises(convirt.runtime.ConfigError,
                          self.base.configure,
                          root)

    def test_config_present(self):
        MEM = 4 * 1024 * 1024
        PATH = '/random/path/to/disk/image'
        root = ET.fromstring(
        """<domain type='kvm' id='2'>
          <maxMemory slots='16' unit='KiB'>{mem}</maxMemory>
          <devices>
            <disk type='file' device='disk' snapshot='no'>
              <source file='{path}'>
              </source>
              <target dev='vdb' bus='virtio'/>
            </disk>
          </devices>
        </domain>""".format(mem=MEM*1024, path=PATH))
        self.assertNotRaises(self.base.configure, root)
        conf = self.base.runtime_config
        self.assertEquals(conf.image_path, PATH)
        self.assertEquals(conf.memory_size_mib, MEM)
