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


import libvirt

import convirt


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

        self.runners = []

        def _fake_create(*args, **kwargs):
            rt = FakeRunner()
            self.runners.append(rt)
            return rt

        conn = convirt.openAuth('convirt:///system', None)
        with monkey.patch_scope([(convirt.api, 'create', _fake_create)]):
            dom = conn.createXML(testlib.minimal_dom_xml(), 0)

        self.assertTrue(dom)
        dom.destroy()
