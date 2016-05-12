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

import logging


from .config import environ
from .domain import Domain
from .xmlfile import XMLFile
from . import connection
from . import doms
from . import errors
from . import monitoring
from . import runner
from . import runtime


_log = logging.getLogger('convirt')


def monitorAllDomains(runr=None):
    """
    Must not require root privileges.
    """
    runr = runner.Subproc if runr is None else runr
    monitoring.watchdog(runr.get_all)


def recoveryAllDomains(runr=None):
    runr = runner.Subproc if runr is None else runr
    conf = environ.current()
    for rt_uuid in runr.get_all():
        _log.debug('trying to recover container %r', rt_uuid)
        xml_file = XMLFile(rt_uuid, conf)
        try:
            Domain.recover(rt_uuid, xml_file.read(), conf)
        except Exception:  # FIXME: too coarse
            _log.exception('failed to recover container %r', rt_uuid)
        else:
            _log.debug('recovered container %r', rt_uuid)
    return doms.get_all()


def openConnection(uri, runr=None):
    runr = runner.Subproc if runr is None else runr
    if uri != 'convirt:///system':
        errors.throw()  # TODO: more specific error?
    return connection.Connection(runr)


def openAuth(uri, auth, flags=0):
    return openConnection(uri)


def openReadOnly(uri):
    errors.throw()  # TODO: more specific error?
