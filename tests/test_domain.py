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


class DomainIdsTests(unittest.TestCase):

    def setUp(self):
        self.guid = uuid.uuid4()
        self.xmldesc = """<?xml version="1.0" encoding="utf-8"?>
        <domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
            <name>testVm</name>
            <uuid>%s</uuid>
        </domain>
        """
        self.dom = convirt.domain.Domain(
            self.xmldesc % str(self.guid)
        )

    def test_ID(self):
        self.assertEqual(self.dom.ID(), self.guid.int)

    def test_UUIDString(self):
        self.assertEqual(self.dom.UUIDString(), str(self.guid))


_MINIMAL_DOM_XML = """<?xml version="1.0" encoding="utf-8"?>
<domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
  <name>testVm</name>
  <uuid>ce051993-3f10-4478-94cf-295c919bf7e3</uuid>
</domain>
"""


class DomainXMLTests(unittest.TestCase):

    def test_XMLDesc(self):
        dom = convirt.domain.Domain(_MINIMAL_DOM_XML)
        self.assertEqual(dom.XMLDesc(0), _MINIMAL_DOM_XML)

    def test_XMLDesc_ignore_flags(self):
        # TODO: provide XML to exercise all the features.
        _TEST_DOM_XML = _MINIMAL_DOM_XML
        dom = convirt.domain.Domain(_TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_UPDATE_CPU),
                                     _TEST_DOM_XML)


class UnsupportedAPITests(unittest.TestCase):

    def test_migrate(self):
        dom = convirt.domain.Domain(_MINIMAL_DOM_XML)
        self.assertRaises(libvirt.libvirtError,
                          dom.migrate,
                          {})
