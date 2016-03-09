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

import uuid
import xml.etree.ElementTree as ET

import libvirt

import convirt
import convirt.config
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


class ConnectionAPITests(testlib.TestCase):

    def setUp(self):
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

    def test_list_all_domains_none(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertEquals(conn.listAllDomains(0), [])

    def test_list_domains_id_none(self):
        conn = convirt.openAuth('convirt:///system', None)
        self.assertEquals(conn.listDomainsID(), [])

    def test_createXML(self):

        self.runners = []

        def _fake_create(*args, **kwargs):
            rt = FakeRunner()
            self.runners.append(rt)
            return rt

        conn = convirt.openAuth('convirt:///system', None)
        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                with monkey.patch_scope([(convirt.api, 'create', _fake_create)]):
                    dom = conn.createXML(testlib.minimal_dom_xml(), 0)

        self.assertTrue(dom)
        dom.destroy()

    def test_recoverAllDomains(self):
        vm_uuid = str(uuid.uuid4())

        def _fake_get_all():
            yield vm_uuid

        def _fake_create(*args, **kwargs):
            return FakeRunner()

        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                xf = convirt.xmlfile.XMLFile(vm_uuid,
                                             convirt.config.current())
                save_xml(xf, testlib.minimal_dom_xml(vm_uuid=vm_uuid))
                with monkey.patch_scope([(convirt.runner, 'get_all',
                                          _fake_get_all),
                                         (convirt.api, 'create', _fake_create),
                                        ]):
                    conn = convirt.openAuth('convirt:///system', None)
                    recovered_doms = conn.recoveryAllDomains()
                    self.assertEquals(len(recovered_doms), 1)
                    self.assertEquals(recovered_doms[0].UUIDString(), vm_uuid)

    def test_recoverAllDomains_with_exceptions(self):
        vm_uuids = [
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4()),
        ]

        def _fake_get_all():
            # mismatch UUID
            return [str(uuid.uuid4())] + vm_uuids[1:]

        def _fake_create(*args, **kwargs):
            return FakeRunner()

        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                for vm_uuid in vm_uuids:
                    xf = convirt.xmlfile.XMLFile(vm_uuid,
                                                 convirt.config.current())
                    save_xml(xf, testlib.minimal_dom_xml(vm_uuid=vm_uuid))

                with monkey.patch_scope([
                    (convirt.runner, 'get_all', _fake_get_all),
                    (convirt.api, 'create', _fake_create),
                ]):
                    conn = convirt.openAuth('convirt:///system', None)
                    recovered_doms = conn.recoveryAllDomains()
                    recovered_uuids = set(vm_uuids[1:])
                    self.assertEquals(len(recovered_doms),
                                      len(recovered_uuids))
                    for dom in recovered_doms:
                        self.assertIn(dom.UUIDString(), recovered_uuids)


class FakeDomain(object):
    def __init__(self, vm_uuid):
        self._vm_uuid = vm_uuid

    def UUIDString(self):
        return self._vm_uuid


class FakeRunner(object):
    def __init__(self):
        self.stopped = False
        self.started = False
        self.setup_done = False
        self.teardown_done = False
        self.configured = False

    def setup(self, *args, **kwargs):
        self.setup_done = True

    def teardown(self, *args, **kwargs):
        self.teardown_done = True

    def start(self, *args, **kwargs):
        self.started = True

    def stop(self):
        self.stopped = True

    def configure(self, *args, **kwargs):
        self.configured = True


def save_xml(xf, xml_str):
    root = ET.fromstring(xml_str)
    xf.save(root)
