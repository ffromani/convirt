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
import unittest

import libvirt

import convirt
import convirt.config.environ
import convirt.connection
import convirt.events
import convirt.runner

from . import monkey
from . import testlib


class WatchdogTests(testlib.RunnableTestCase):

    def test_domain_disappeared(self):
        evt = libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE

        delivered = []
        def _cb(*args, **kwargs):
            delivered.append(args)

        def _fake_get_all():
            return []

        conn = convirt.connection.Connection()
        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                dom = conn.createXML(_XML_DESC % str(uuid.uuid4()), 0)
                conn.domainEventRegisterAny(dom, evt, _cb, None)
                with monkey.patch_scope([(convirt.runner, 'get_all', _fake_get_all)]):
                    convirt.monitorAllDomains()

        self.assertEquals(delivered, [(
            libvirt.VIR_DOMAIN_EVENT_STOPPED,
            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN,
        )])


_XML_DESC = """<?xml version="1.0" encoding="utf-8"?>
    <domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
    <name>testVm</name>
    <uuid>%s</uuid>
    <maxMemory>0</maxMemory>
    <devices>
      <emulator>rkt</emulator>
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
    </domain>
"""



def _handler(*args, **kwargs):
    pass
