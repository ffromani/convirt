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

from . import doms
from . import events
from . import runner

import libvirt


def watchdog():
    found = set(vm_uuid for vm_uuid in runner.get_all())
    for dom in doms.get_all():
        if dom.UUIDString() not in found:
            dom.events.fire(libvirt.VIR_DOMAIN_EVENT_STOPPED,
                            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN,
                            0)  # unused
