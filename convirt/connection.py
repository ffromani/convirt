from __future__ import absolute_import

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

from . import config
from . import domain
from . import doms
from . import errors
from . import runner
from . import xmlfile


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

    def listAllDomains(self, flags=0):
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
    def createXML(self, domxml, flags):
        # flags are unused
        return domain.Domain.create(domxml)

    def getLibVersion(self):
        return 0x001002018  # TODO

    def recoveryAllDomains(self):
        conf = config.current()
        for vm_uuid in runner.get_all():
            self._log.debug('trying to recover container %r', vm_uuid)
            xml_file = xmlfile.XMLFile(vm_uuid, conf)
            try:
                domain.Domain.recover(vm_uuid, xml_file.read(), conf)
            except Exception:  # FIXME: too coarse
                self._log.exception('failed to recover container %r',
                                    vm_uuid)
            else:
                self._log.debug('recovered container %r', vm_uuid)
        return doms.get_all()

    def __getattr__(self, name):
        # virConnect does not expose non-callable attributes.
        return self._fake_method
    
    def _fake_method(self, *args):
        errors.throw()
