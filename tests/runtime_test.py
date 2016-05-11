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

import uuid
import xml.etree.ElementTree as ET

import convirt
import convirt.command
import convirt.config
import convirt.config.environ
import convirt.runtime
import convirt.runtimes

from . import monkey
from . import testlib


class RaisingPath(object):
    def __init__(self):
        self.cmd = None

    def get(self):
        raise convirt.command.NotFound()


class RuntimeContainerAvailabilityTests(testlib.TestCase):

    def test_raising(self):
        with monkey.patch_scope(
            [(convirt.runtimes.ContainerRuntime, '_PATH', RaisingPath())]
        ):
            self.assertFalse(convirt.runtimes.ContainerRuntime.available())

    def test_not_available(self):
        with monkey.patch_scope(
            [(convirt.runtimes.ContainerRuntime, '_PATH', testlib.NonePath())]
        ):
            self.assertFalse(convirt.runtimes.ContainerRuntime.available())

    def test_available(self):
        with monkey.patch_scope(
            [(convirt.runtimes.ContainerRuntime, '_PATH', testlib.TruePath())]
        ):
            self.assertTrue(convirt.runtimes.ContainerRuntime.available())


class RuntimeContainerUnimplementedAPITests(testlib.TestCase):

    def setUp(self):
        self.base = convirt.runtimes.ContainerRuntime(
            convirt.config.environ.current())

    def test_unit_name(self):
        self.assertTrue(self.base.unit_name())  # TODO: improve

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

    def test_setup_runtime(self):
        self.assertNotRaises(
            convirt.runtimes.ContainerRuntime.setup_runtime())

    def test_teardown_runtime(self):
        self.assertNotRaises(
            convirt.runtimes.ContainerRuntime.teardown_runtime())

    def test_configure_runtime(self):
        self.assertNotRaises(
            convirt.runtimes.ContainerRuntime.configure_runtime())


class RuntimeContainerConfigureTests(testlib.TestCase):

    def setUp(self):
        self.vm_uuid = str(uuid.uuid4())
        self.conf = convirt.config.environ.current()
        self.base = convirt.runtimes.ContainerRuntime(
            self.conf, rt_uuid=self.vm_uuid)

    def test_missing_content(self):
        root = ET.fromstring("<domain type='kvm' id='2'></domain>")
        self.assertRaises(convirt.runtimes.ConfigError,
                          self.base.configure,
                          root)

    def test_missing_memory(self):
        root = ET.fromstring(testlib.only_disk_dom_xml())
        self.assertRaises(convirt.runtimes.ConfigError,
                          self.base.configure,
                          root)

    def test_missing_disk(self):
        root = ET.fromstring(testlib.only_mem_dom_xml())
        self.assertRaises(convirt.runtimes.ConfigError,
                          self.base.configure,
                          root)

    def test_disk_source_not_file(self):
        root = ET.fromstring(testlib.disk_file_malformed_dom_xml())
        self.assertRaises(convirt.runtimes.ConfigError,
                          self.base.configure,
                          root)

    def test_bridge_down(self):
        root = ET.fromstring(testlib.bridge_down_dom_xml())
        with testlib.global_conf(net_fallback=False) as conf:
            base = convirt.runtimes.ContainerRuntime(
                conf, rt_uuid=self.vm_uuid)
            self.assertRaises(convirt.runtimes.ConfigError,
                              base.configure,
                              root)

    def test_bridge_no_source(self):
        root = ET.fromstring(testlib.bridge_no_source_dom_xml())
        with testlib.global_conf(net_fallback=False) as conf:
            base = convirt.runtimes.ContainerRuntime(
                conf, rt_uuid=self.vm_uuid)
            self.assertRaises(convirt.runtimes.ConfigError,
                              base.configure,
                              root)

    def test_config_present(self):
        MEM = 4 * 1024 * 1024
        PATH = '/random/path/to/disk/image'
        root = ET.fromstring("""
        <domain type='kvm' id='2'>
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
        self.assertEquals(conf.network, None)

    def test_config_ovirt_vm(self):
        root = ET.fromstring(testlib.full_dom_xml())
        self.assertNotRaises(self.base.configure, root)
        conf = self.base.runtime_config
        self.assertTrue(conf.image_path)
        self.assertTrue(conf.memory_size_mib)
        self.assertEquals(conf.network, "ovirtmgmt")

    # TODO: test error paths in configure()


class RuntimeAPITests(testlib.RunnableTestCase):

    def test_create_supported(self):
        conf = convirt.config.environ.current()
        self.assertTrue(convirt.runtime.create('rkt', conf))

    def test_create_unsupported(self):
        conf = convirt.config.environ.current()
        self.assertRaises(convirt.runtime.Unsupported,
                          convirt.runtime.create,
                          'docker',
                          conf)

    def test_supported(self):
        self.assertIn('rkt', convirt.runtime.supported(register=False))

    def test_setup_register(self):
        self.assertIn('rkt', convirt.runtime.supported())

    def test_setup(self):
        convirt.runtime.clear()
        self.assertEqual(
            convirt.runtime.supported(register=False),
            frozenset())
        self.assertNotRaises(convirt.runtime.setup())
        self.assertTrue(convirt.runtime.supported(register=False))

    def test_setup_twice(self):
        convirt.runtime.clear()
        self.assertEqual(
            convirt.runtime.supported(register=False),
            frozenset())
        self.assertNotRaises(convirt.runtime.setup())
        self.assertRaises(convirt.runtime.SetupError,
                          convirt.runtime.setup)

    def test_teardown(self):
        convirt.runtime.clear()
        self.assertEqual(
            convirt.runtime.supported(register=False),
            frozenset())
        self.assertNotRaises(convirt.runtime.setup())
        self.assertNotRaises(convirt.runtime.teardown())
        self.assertEqual(
            convirt.runtime.supported(register=False),
            frozenset())

    def test_teardown_without_setup(self):
        convirt.runtime.clear()
        self.assertRaises(convirt.runtime.SetupError,
                          convirt.runtime.teardown)

    def test_teardown_twice(self):
        convirt.runtime.clear()
        self.assertEqual(
            convirt.runtime.supported(register=False),
            frozenset())
        self.assertNotRaises(convirt.runtime.setup())
        self.assertNotRaises(convirt.runtime.teardown())
        self.assertRaises(convirt.runtime.SetupError,
                          convirt.runtime.teardown)
