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


import uuid
import unittest

import libvirt

import convirt
import convirt.domain
import convirt.doms


class DomainIdsTests(unittest.TestCase):

    def setUp(self):
        self.guid = uuid.uuid4()
        self.xmldesc = """<?xml version="1.0" encoding="utf-8"?>
        <domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
            <name>testVm</name>
            <uuid>%s</uuid>
            <maxMemory>0</maxMemory>
            <devices>
                <emulator>rkt</emulator>
            </devices>
        </domain>
        """
        self.dom = convirt.domain.Domain(
            self.xmldesc % str(self.guid)
        )

    def test_ID(self):
        self.assertEqual(self.dom.ID(), self.guid.int)

    def test_UUIDString(self):
        self.assertEqual(self.dom.UUIDString(), str(self.guid))


def _minimal_dom_xml():
    return """<?xml version="1.0" encoding="utf-8"?>
<domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
  <name>testVm</name>
  <uuid>%s</uuid>
  <maxMemory>0</maxMemory>
  <devices>
    <emulator>rkt</emulator>
    <disk type='file' device='disk' snapshot='no'>
      <driver name='qemu' type='raw' cache='none' error_policy='stop' io='threads'/>
      <source file='/rhev/data-center/00000001-0001-0001-0001-00000000027f/43db3789-bb16-40bd-a9fc-3cced1b23ea6/images/90bece76-2df6-4a88-bfc8-f6f7461b7b8b/844e5378-6700-45ba-a846-67eba730e24b'>
        <seclabel model='selinux' labelskip='yes'/>
      </source>
      <backingStore/>
      <target dev='vda' bus='virtio'/>
      <serial>90bece76-2df6-4a88-bfc8-f6f7461b7b8b</serial>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
    </disk>
  </devices>
</domain>
""" % (str(uuid.uuid4()))


class DomainXMLTests(unittest.TestCase):

    def test_XMLDesc(self):
        dom_xml = _minimal_dom_xml()
        dom = convirt.domain.Domain(dom_xml)
        self.assertEqual(dom.XMLDesc(0), dom_xml)

    def test_XMLDesc_ignore_flags(self):
        # TODO: provide XML to exercise all the features.
        _TEST_DOM_XML = _minimal_dom_xml()
        dom = convirt.domain.Domain(_TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_UPDATE_CPU),
                                     _TEST_DOM_XML)


class UnsupportedAPITests(unittest.TestCase):

    def test_migrate(self):
        dom = convirt.domain.Domain(_minimal_dom_xml())
        self.assertRaises(libvirt.libvirtError,
                          dom.migrate,
                          {})


class RegistrationTests(unittest.TestCase):

    def test_destroy_registered(self):
        dom = convirt.domain.Domain.create(_minimal_dom_xml())
        existing_doms = convirt.doms.get_all()
        self.assertEquals(len(existing_doms), 1)
        self.assertEquals(dom.ID, existing_doms[0].ID)
        dom.destroy()
        self.assertEquals(convirt.doms.get_all(), [])

    def test_destroy_unregistered(self):
        dom = convirt.domain.Domain(_minimal_dom_xml())
        self.assertEquals(convirt.doms.get_all(), [])
        self.assertRaises(libvirt.libvirtError,
                          dom.destroy)
