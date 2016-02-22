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


import unittest

import convirt
import convirt.api

from . import monkey
from . import testlib


class FunctionsTests(unittest.TestCase):

    def test_no_runtimes_supported(self):
        with monkey.patch_scope([(convirt.rkt.Rkt, '_PATH',
                                  testlib.NonePath())]):
            self.assertFalse(convirt.api.supported())

    def test_supported(self):
        with monkey.patch_scope([(convirt.rkt.Rkt, '_PATH',
                                  testlib.TruePath())]):
            self.assertTrue(convirt.api.supported())
