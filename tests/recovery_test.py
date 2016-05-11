#
# Copyright 2016 Red Hat, Inc.
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
import convirt.config
import convirt.config.environ
import convirt.doms
import convirt.runner
import convirt.xmlfile


from . import monkey
from . import testlib


class RecoveryTests(testlib.FakeRunnableTestCase):

    def setUp(self):
        super(RecoveryTests, self).setUp()
        convirt.doms.clear()

    def tearDown(self):
        convirt.doms.clear()

    def test_recoverAllDomains(self):
        vm_uuid = str(uuid.uuid4())

        class FakeRunner(object):
            @classmethod
            def get_all(cls):
                yield vm_uuid

        def _fake_create(*args, **kwargs):
            return testlib.FakeRunner()

        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                xf = convirt.xmlfile.XMLFile(vm_uuid,
                                             convirt.config.environ.current())
                save_xml(xf, testlib.minimal_dom_xml(vm_uuid=vm_uuid))
                with monkey.patch_scope([
                    (convirt.runtime, 'create', _fake_create),
                ]):
                    recovered_doms = convirt.recoveryAllDomains(FakeRunner)
                    self.assertEquals(len(recovered_doms), 1)
                    self.assertEquals(recovered_doms[0].UUIDString(), vm_uuid)

    def test_recoverAllDomains_with_exceptions(self):
        vm_uuids = [
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4()),
        ]

        class FakeRunner(object):
            @classmethod
            def get_all(cls):
                # mismatch UUID
                return [str(uuid.uuid4())] + vm_uuids[1:]

        def _fake_create(*args, **kwargs):
            return testlib.FakeRunner()

        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                for vm_uuid in vm_uuids:
                    xf = convirt.xmlfile.XMLFile(
                        vm_uuid,
                        convirt.config.environ.current())
                    save_xml(xf, testlib.minimal_dom_xml(vm_uuid=vm_uuid))

                with monkey.patch_scope([
                    (convirt.runtime, 'create', _fake_create),
                ]):
                    recovered_doms = convirt.recoveryAllDomains(FakeRunner)
                    recovered_uuids = set(vm_uuids[1:])
                    self.assertEquals(len(recovered_doms),
                                      len(recovered_uuids))
                    for dom in recovered_doms:
                        self.assertIn(dom.UUIDString(), recovered_uuids)


def save_xml(xf, xml_str):
    root = ET.fromstring(xml_str)
    xf.save(root)
