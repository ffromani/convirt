
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

import libvirt

from . import domain
from . import doms
from . import errors


class Connection(object):

    _log = logging.getLogger('convirt.Connection')

    def __init__(self):
        self._event_handlers = {}

    def close(self):
        """
        Does nothing succesfully
        """

#    def domainEventRegisterAny(self, dom, eventID, cb, opaque):
#        pass

    def listAllDomains(self, flags):
        # flags are unused
        return doms.get_all()

    def listDomainsID(self):
        return [dom.ID() for dom in doms.get_all()]

    def lookupByUUIDString(self, guid):
        try:
            return doms.get_by_uuid(guid)
        except KeyError:
            errors.throw(code=libvirt.VIR_ERR_NO_DOMAIN)

    def lookupByID(self, intid):
        # hack?
        # python supports 128-bit ints, so this is a legitimate int in python.
        return self.lookupByUUIDString(str(uuid.UUID(int=intid)))

#    def getAllDomainStats(self, flags):
#        pass
#
#    def domainListGetStats(self, doms, flags):
#        pass
#
#    def createXML(self, domxml, flags):
#        return domain.Domain(domxml)

    def getLibVersion(self):
        return 0x001002018  # TODO

    def __getattr__(self, name):
        # virConnect does not expose non-callable attributes.
        return self._fake_method
    
    def _fake_method(self, *args):
        errors.throw()
