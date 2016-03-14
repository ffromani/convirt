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

import contextlib
import os
import uuid
import unittest
import xml.etree.ElementTree as ET

import convirt
import convirt.config
import convirt.config.environ
import convirt.xmlfile

from . import monkey
from . import testlib


class XMLFileTests(testlib.TestCase):

    def setUp(self):
        self.vm_uuid = str(uuid.uuid4())

    @contextlib.contextmanager
    def test_env(self):
        with testlib.named_temp_dir() as tmp_dir:
            with testlib.global_conf(run_dir=tmp_dir):
                yield convirt.xmlfile.XMLFile(
                    self.vm_uuid,
                    convirt.config.environ.current()
                )

    def test_fails_without_conf(self):
        self.assertRaises(convirt.xmlfile.UnconfiguredXML,
                          convirt.xmlfile.XMLFile,
                          self.vm_uuid,
                          None)

    def test_path(self):
        with self.test_env() as xf:
            self.assertTrue(xf.path.endswith('xml'))
            self.assertIn(self.vm_uuid, xf.path)

    def test_save(self):
        root = ET.fromstring(testlib.minimal_dom_xml())
        with self.test_env() as xf:
            conf = convirt.config.environ.current()
            self.assertEquals(os.listdir(conf.run_dir), [])
            self.assertNotRaises(xf.save, root)
            self.assertTrue(len(os.listdir(conf.run_dir)), 1)

    def test_load(self):
        xml_data = testlib.minimal_dom_xml()
        root = ET.fromstring(xml_data)
        with self.test_env() as xf:
            xf.save(root)
            new_root = xf.load()
            xml_copy = convirt.xmlfile.XMLFile.encode(new_root)
            # FIXME: nasty trick to tidy up the XML
            xml_ref = convirt.xmlfile.XMLFile.encode(root)
            self.assertEquals(xml_ref, xml_copy)

    def test_clear(self):
        xml_data = testlib.minimal_dom_xml()
        root = ET.fromstring(xml_data)
        with self.test_env() as xf:
            xf.save(root)
            conf = convirt.config.environ.current()
            self.assertTrue(len(os.listdir(conf.run_dir)), 1)
            self.assertNotRaises(xf.clear)
            self.assertEquals(os.listdir(conf.run_dir), [])
