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

import logging
import uuid
import xml.etree.ElementTree as ET

import libvirt


from . import errors
from . import doms


class Domain(object):

    _log = logging.getLogger('convirt.Domain')

    def __init__(self, xmldesc):
        self._xmldesc = xmldesc
        self._root = ET.fromstring(xmldesc)
        self._guid = uuid.UUID(self._root.find('./uuid').text)
        doms.add(self)  # TODO racy. But it is a problem for us?

    def destroy(self):
        doms.remove(self.UUIDString())

#    def reset(self, flags):
#        pass

    def ID(self):
        return self._guid.int

    def UUIDString(self):
        return str(self._guid)

    def XMLDesc(self, flags):
        return self._xmldesc

#    def blockInfo(self, path, flags):
#        pass
#
#    def setTime(self, time):
#        pass
#
#    def info(self):
#        pass

    def __getattr__(self, name):
        # virDomain does not expose non-callable attributes.
        return self._fake_method
    
    def _fake_method(self, *args):
        errors.throw()
