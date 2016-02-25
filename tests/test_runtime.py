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
