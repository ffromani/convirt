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

import os
import tempfile
import uuid

import convirt
import convirt.fs

from . import testlib


class ReadFileTests(testlib.TestCase):

    def test_read_existing_file(self):
        content = str(uuid.uuid4())
        with tempfile.NamedTemporaryFile() as f:
            f.write(content.encode('ascii'))
            f.flush()
            self.assertEqual(content,
                             convirt.fs.read_file(f.name))

    def test_read_unexisting_file(self):
        path = '/most/likely/does/not/exist'
        self.assertRaises(IOError,
                          convirt.fs.read_file,
                          path)


class RMFileTests(testlib.TestCase):

    def test_rm_file_once(self):
        with testlib.named_temp_dir() as tmp_dir:
            path = os.path.join(tmp_dir, "foobar")
            with open(path, 'wt') as f:
                f.write('%s\n' % str(uuid.uuid4()))
            self.assertEquals(os.listdir(tmp_dir), ['foobar'])
            convirt.fs.rm_file(path)
            self.assertEquals(os.listdir(tmp_dir), [])

    def test_rm_file_twice(self):
        with testlib.named_temp_dir() as tmp_dir:
            path = os.path.join(tmp_dir, "foobar")
            with open(path, 'wt') as f:
                f.write('%s\n' % str(uuid.uuid4()))
            self.assertEquals(os.listdir(tmp_dir), ['foobar'])
            convirt.fs.rm_file(path)
            self.assertEquals(os.listdir(tmp_dir), [])
            self.assertNotRaises(convirt.fs.rm_file, path)
            self.assertEquals(os.listdir(tmp_dir), [])

    def test_rm_file_fails(self):
        self.assertNotEqual(os.geteuid(), 0)
        self.assertRaises(OSError,
                          convirt.fs.rm_file,
                          '/var/log/lastlog')
