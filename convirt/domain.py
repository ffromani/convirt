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


from . import api
from . import errors
from . import doms
from . import runtime


class Domain(object):

    _log = logging.getLogger('convirt.Domain')

    @classmethod
    def create(cls, xmldesc, conf=None):
        inst = cls(xmldesc, conf)
        inst._startup()
        doms.add(inst)
        return inst

    def __init__(self, xmldesc, conf=None):
        self._xmldesc = xmldesc
        self._root = ET.fromstring(xmldesc)
        self._vm_uuid = uuid.UUID(self._root.find('./uuid').text)
        self._rt = api.create(self._root.find('./devices/emulator').text,
                              vm_uuid=self.UUIDString(),
                              conf=conf)

    def destroy(self):
        vm_uuid = self.UUIDString()

        try:
            self._shutdown()
            doms.remove(vm_uuid)
        except runtime.OperationFailed:
            errors.throw()  # FIXME: specific error
        except KeyError:
            errors.throw()  # FIXME: specific error

    def reset(self, flags):
        self._rt.stop()
        self._rt.start()

    def ID(self):
        return self._vm_uuid.int

    def UUIDString(self):
        return str(self._vm_uuid)

    def XMLDesc(self, flags):
        # TODO: raise warning to signal we ignore flags?
        return self._xmldesc

#    def blockInfo(self, path, flags):
#        pass
#
#    def setTime(self, time):
#        pass
#
#    def info(self):
#        pass

    def _startup(self):
        self._rt.setup()
        self._rt.configure(self._root)
        self._rt.start()

    def _shutdown(self):
        self._rt.stop()
        self._rt.teardown()

    def __getattr__(self, name):
        # virDomain does not expose non-callable attributes.
        return self._fake_method
    
    def _fake_method(self, *args):
        errors.throw()
