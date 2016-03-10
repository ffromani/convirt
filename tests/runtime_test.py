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
import convirt.config
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
        self.base = convirt.runtime.Base(convirt.config.current())

    def test_unit_name(self):
        self.assertTrue(self.base.unit_name())  # TODO: improve



class RuntimeBaseAPITests(testlib.TestCase):

    def setUp(self):
        self.base = convirt.runtime.Base(convirt.config.current())

    def test_start(self):
        self.assertRaises(NotImplementedError, self.base.start, '')

    def test_resync(self):
        self.assertRaises(NotImplementedError, self.base.resync)

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

    def test_config_ovirt_vm(self):
        root = ET.fromstring(
        """<?xml version="1.0" encoding="utf-8"?>
<domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
        <name>a_c7_2</name>
        <uuid>338175a6-44e7-45d0-8321-2c6f2d5b3d6b</uuid>
        <memory>4194304</memory>
        <currentMemory>4194304</currentMemory>
        <maxMemory slots="16">4294967296</maxMemory>
        <vcpu current="2">16</vcpu>
        <devices>
                <channel type="unix">
                        <target name="com.redhat.rhevm.vdsm" type="virtio"/>
                        <source mode="bind" path="/var/lib/libvirt/qemu/channels/338175a6-44e7-45d0-8321-2c6f2d5b3d6b.com.redhat.rhevm.vdsm"/>
                </channel>
                <channel type="unix">
                        <target name="org.qemu.guest_agent.0" type="virtio"/>
                        <source mode="bind" path="/var/lib/libvirt/qemu/channels/338175a6-44e7-45d0-8321-2c6f2d5b3d6b.org.qemu.guest_agent.0"/>
                </channel>
                <input bus="ps2" type="mouse"/>
                <emulator>rkt</emulator>
                <memballoon model="none"/>
                <video>
                        <model heads="1" ram="65536" type="qxl" vgamem="16384" vram="32768"/>
                </video>
                <graphics autoport="yes" passwd="*****" passwdValidTo="1970-01-01T00:00:01" port="-1" tlsPort="-1" type="spice">
                        <listen network="vdsm-ovirtmgmt" type="network"/>
                </graphics>
                <interface type="bridge">
                        <mac address="00:1a:4a:16:01:57"/>
                        <model type="virtio"/>
                        <source bridge="ovirtmgmt"/>
                        <filterref filter="vdsm-no-mac-spoofing"/>
                        <link state="up"/>
                        <bandwidth/>
                </interface>
                <disk device="cdrom" snapshot="no" type="file">
                        <source file="" startupPolicy="optional"/>
                        <target bus="ide" dev="hdc"/>
                        <readonly/>
                        <serial/>
                </disk>
                <disk device="disk" snapshot="no" type="file">
                        <source file="/rhev/data-center/00000001-0001-0001-0001-00000000027f/43db3789-bb16-40bd-a9fc-3cced1b23ea6/images/27101aac-10ec-468a-aaf5-694c663b2c33/19bb423f-7db0-4cd1-9fe9-5aa3d4d8c1af"/>
                        <target bus="virtio" dev="vda"/>
                        <serial>27101aac-10ec-468a-aaf5-694c663b2c33</serial>
                        <boot order="1"/>
                        <driver cache="none" error_policy="stop" io="threads" name="qemu" type="raw"/>
                </disk>
                <channel type="spicevmc">
                        <target name="com.redhat.spice.0" type="virtio"/>
                </channel>
        </devices>
        <metadata>
                <ovirt:qos/>
        </metadata>
        <os>
                <type arch="x86_64" machine="pc-i440fx-rhel7.2.0">hvm</type>
                <smbios mode="sysinfo"/>
        </os>
        <sysinfo type="smbios">
                <system>
                        <entry name="manufacturer">oVirt</entry>
                        <entry name="product">oVirt Node</entry>
                        <entry name="version">7-2.1511.el7.centos.2.10</entry>
                        <entry name="serial">0A9C980E-6B95-3D34-C5AC-40167EB07D87</entry>
                        <entry name="uuid">338175a6-44e7-45d0-8321-2c6f2d5b3d6b</entry>
                </system>
        </sysinfo>
        <clock adjustment="0" offset="variable">
                <timer name="rtc" tickpolicy="catchup"/>
                <timer name="pit" tickpolicy="delay"/>
                <timer name="hpet" present="no"/>
        </clock>
        <features>
                <acpi/>
        </features>
        <cpu match="exact">
                <model>Opteron_G2</model>
                <topology cores="1" sockets="16" threads="1"/>
                <numa>
                        <cell cpus="0,1" memory="4194304"/>
                </numa>
        </cpu>
        <numatune>
                <memory mode="interleave" nodeset="0"/>
        </numatune>
</domain>""")
        self.assertNotRaises(self.base.configure, root)
        conf = self.base.runtime_config
        self.assertTrue(conf.image_path)


class RMFileTests(testlib.TestCase):

    def test_rm_file_once(self):
        with testlib.named_temp_dir() as tmp_dir:
            path = os.path.join(tmp_dir, "foobar")
            with open(path, 'wt') as f:
                f.write('%s\n' % str(uuid.uuid4()))
            self.assertEquals(os.listdir(tmp_dir), ['foobar'])
            convirt.runtime.rm_file(path)
            self.assertEquals(os.listdir(tmp_dir), [])

    def test_rm_file_twice(self):
        with testlib.named_temp_dir() as tmp_dir:
            path = os.path.join(tmp_dir, "foobar")
            with open(path, 'wt') as f:
                f.write('%s\n' % str(uuid.uuid4()))
            self.assertEquals(os.listdir(tmp_dir), ['foobar'])
            convirt.runtime.rm_file(path)
            self.assertEquals(os.listdir(tmp_dir), [])
            self.assertNotRaises(convirt.runtime.rm_file, path)
            self.assertEquals(os.listdir(tmp_dir), [])

    def test_rm_file_fails(self):
        self.assertNotEqual(os.geteuid(), 0)
        self.assertRaises(OSError,
                          convirt.runtime.rm_file,
                          '/var/log/lastlog')
