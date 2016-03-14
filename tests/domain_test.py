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

from contextlib import contextmanager
import uuid
import unittest

import libvirt

import convirt
import convirt.api
import convirt.command
import convirt.domain
import convirt.doms
import convirt.rkt


from . import monkey
from . import testlib


class DomainIdsTests(testlib.RunnableTestCase):

    def setUp(self):
        super(DomainIdsTests, self).setUp()
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
            self.xmldesc % str(self.guid),
            convirt.config.environ.current()
        )

    def test_ID(self):
        self.assertEqual(self.dom.ID(), self.guid.int)

    def test_UUIDString(self):
        self.assertEqual(self.dom.UUIDString(), str(self.guid))


class DomainXMLTests(testlib.RunnableTestCase):

    def test_XMLDesc(self):
        dom_xml = testlib.minimal_dom_xml()
        dom = convirt.domain.Domain(dom_xml,
                                    convirt.config.environ.current())
        self.assertEqual(dom.XMLDesc(0), dom_xml)

    def test_XMLDesc_ignore_flags(self):
        # TODO: provide XML to exercise all the features.
        _TEST_DOM_XML = testlib.minimal_dom_xml()
        dom = convirt.domain.Domain(_TEST_DOM_XML,
                                    convirt.config.environ.current())
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE),
                                     _TEST_DOM_XML)
        self.assertEqual(dom.XMLDesc(libvirt.VIR_DOMAIN_XML_UPDATE_CPU),
                                     _TEST_DOM_XML)


class DomainAPITests(testlib.FakeRunnableTestCase):

    def test_reset(self):
        self.dom.reset(0)

        self.assertEquals(len(self.runners), 1)
        self.assertTrue(self.runners[0].started)
        self.assertTrue(self.runners[0].stopped)

    def test_controlInfo(self):
        info = self.dom.controlInfo()
        self.assertEquals(len(info), 3)
        # TODO: more testing

    def test_vcpus(self):
        # TODO: meaningful test
        self.assertNotRaises(self.dom.vcpus)


class UnsupportedAPITests(testlib.RunnableTestCase):

    def test_migrate(self):
        dom = convirt.domain.Domain(testlib.minimal_dom_xml(),
                                    convirt.config.environ.current())
        self.assertRaises(libvirt.libvirtError,
                          dom.migrate,
                          {})


class RegistrationTests(testlib.RunnableTestCase):

    def test_destroy_registered(self):
        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            dom = convirt.domain.Domain.create(
                testlib.minimal_dom_xml(), conf)

        existing_doms = convirt.doms.get_all()
        self.assertEquals(len(existing_doms), 1)
        self.assertEquals(dom.ID, existing_doms[0].ID)
        dom.destroy()
        self.assertEquals(convirt.doms.get_all(), [])

    def test_destroy_unregistered(self):
        # you need to call create() to register into `doms'.
        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            dom = convirt.domain.Domain(testlib.minimal_dom_xml(), conf)

        self.assertEquals(convirt.doms.get_all(), [])
        self.assertRaises(libvirt.libvirtError, dom.destroy)

    def test_destroy_unregistered_forcefullt(self):
        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            dom = convirt.domain.Domain.create(
                testlib.minimal_dom_xml(), conf)

        convirt.doms.remove(dom.UUIDString())
        self.assertRaises(libvirt.libvirtError, dom.destroy)


class RecoveryTests(testlib.TestCase):

    def setUp(self):
        convirt.doms.clear()
        self.runtime = None

    def test_recover(self):
        vm_uuid = str(uuid.uuid4())

        with testlib.named_temp_dir() as tmp_dir:
            conf = testlib.make_conf(run_dir=tmp_dir)
            with monkey.patch_scope([(convirt.api, 'create',
                                      self._fake_create)]):
                dom = convirt.domain.Domain.recover(
                    vm_uuid, testlib.minimal_dom_xml(vm_uuid), conf)

        existing_doms = convirt.doms.get_all()
        self.assertEquals(len(existing_doms), 1)
        self.assertEquals(existing_doms[0].UUIDString(), vm_uuid)
        self.assertTrue(self.runtime.resynced)

    def _fake_create(self, rt, *args, **kwargs):
        self.runtime = ResyncingRuntime()
        return self.runtime


class ResyncingRuntime(object):

    def __init__(self):
        self.uuid = '00000000-0000-0000-0000-000000000000'
        self.resynced = False

    @classmethod
    def available(cls):
        return True

    def resync(self):
        self.resynced = True

    def unit_name(self):
        raise AssertionError("should not be called")

    def configure(self, xml_tree):
        raise AssertionError("should not be called")

    def start(self, target=None):
        raise AssertionError("should not be called")

    def stop(self):
        raise AssertionError("should not be called")

    def status(self):
        raise AssertionError("should not be called")

    def runtime_name(self):
        raise AssertionError("should not be called")

    def setup(self):
        raise AssertionError("should not be called")

    def teardown(self):
        raise AssertionError("should not be called")

    @property
    def runtime_config(self):
        raise AssertionError("should not be called")
