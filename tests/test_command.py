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

import errno
import os
import subprocess
import unittest

import convirt
import convirt.command

from . import monkey
from . import testlib


# borrowed from Vdsm sources - http://www.ovirt.org

# originally CommandPathTests in utilTests.py
class PathTests(testlib.TestCase):
    def test_name(self):
        CMD = 'sh'
        cp = convirt.command.Path(CMD)
        self.assertEqual(cp.name, CMD)

    def test_existing(self):
        cp = convirt.command.Path('sh', paths=['utter nonsense', '/bin/'])
        self.assertEquals(cp.cmd(), '/bin/sh')

    def test_existing_without_paths(self):
        cp = convirt.command.Path('sh')
        output = str(subprocess.check_output(['which', 'sh']))
        self.assertIn(cp.cmd(), output)

    def test_missing(self):
        cp = convirt.command.Path('nonsense')
        self.assertRaises(convirt.command.NotFound,
                          cp.cmd)

    def test_missing_path(self):
        with monkey.patch_scope([(os, 'environ', {})]):
            cp = convirt.command.Path('sh')
            self.assertRaises(convirt.command.NotFound, cp.cmd)
