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

import libvirt

import convirt
import convirt.config
import convirt.config.environ
import convirt.doms
import convirt.runner
import convirt.xmlfile


from . import monkey
from . import testlib


class OpenConnectionTests(testlib.TestCase):

    def test_wrong_session(self):
        self.assertRaises(libvirt.libvirtError,
                          convirt.openAuth,
                          'qemu:///system',
                          None)

    def test_open_auth_none(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertTrue(conn)

    def test_open_auth_ignored(self):
        def req(credentials, user_data):
            for cred in credentials:
                if cred[0] == libvirt.VIR_CRED_AUTHNAME:
                    cred[4] = 'convirt'
                elif cred[0] == libvirt.VIR_CRED_PASSPHRASE:
                    cred[4] = 'ignored'
            return 0

        auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE],
                req, None]

        conn = convirt.openAuth('convirt:///system', auth)
        self.assertTrue(conn)

    def test_close(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertNotRaises(conn.close)


class ConnectionAPITests(testlib.FakeRunnableTestCase):

    def setUp(self):
        super(ConnectionAPITests, self).setUp()
        convirt.doms.clear()

    def tearDown(self):
        convirt.doms.clear()

    def test_get_lib_version(self):
        conn = convirt.openAuth('convirt:///system', None)
        ver = conn.getLibVersion()
        self.assertGreater(ver, 0)

    def test_lookup_by_name_missing(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertRaises(libvirt.libvirtError,
                          conn.lookupByName,
                          "foobar")

    def test_lookup_by_id_missing(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertRaises(libvirt.libvirtError,
                          conn.lookupByID,
                          42)

    def test_lookup_by_uuid_string(self):
        convirt.doms.add(self.dom)
        conn = convirt.openAuth('convirt:///system', None)
        guid = self.dom.UUIDString()
        dom = conn.lookupByUUIDString(guid)
        self.assertEquals(dom.UUIDString(), guid)

    def test_list_all_domains_none(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertEquals(conn.listAllDomains(0), [])

    def test_list_domains_id_none(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertEquals(conn.listDomainsID(), [])

    def test_createXML(self):

        self.runners = []

        def _fake_create(*args, **kwargs):
            rt = testlib.FakeRunner()
            self.runners.append(rt)
            return rt

        conn = convirt.openAuth('convirt:///system', None)
        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                with monkey.patch_scope([(convirt.api, 'create', _fake_create)]):
                    dom = conn.createXML(testlib.minimal_dom_xml(), 0)

        self.assertTrue(dom)
        dom.destroy()


class FakeDomain(object):
    def __init__(self, vm_uuid):
        self._vm_uuid = vm_uuid

    def UUIDString(self):
        return self._vm_uuid


def save_xml(xf, xml_str):
    root = ET.fromstring(xml_str)
    xf.save(root)
