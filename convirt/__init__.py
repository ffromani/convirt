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

import functools
import logging


from .config import environ
from .domain import Domain
from .xmlfile import XMLFile
from . import command
from . import connection
from . import doms
from . import errors
from . import monitoring
from . import runner

# FIXME
from . import xmlconstants as XML
# make pyflakes happy
XML

_log = logging.getLogger('convirt')


def monitorAllDomains(repo=None):
    """
    Must not require root privileges.
    """
    repo = command.Repo() if repo is None else repo
    get_vm_uuids = functools.partial(runner.Runner.get_all, repo)
    monitoring.watchdog(get_vm_uuids)


def recoveryAllDomains(repo=None):
    conf = environ.current()
    repo = command.Repo() if repo is None else repo
    for rt_uuid in runner.Runner.get_all(repo):
        _log.debug('trying to recover container %r', rt_uuid)
        xml_file = XMLFile(rt_uuid, conf)
        try:
            Domain.recover(rt_uuid, xml_file.read(), conf, repo)
        except Exception:  # FIXME: too coarse
            _log.exception('failed to recover container %r', rt_uuid)
            logging.exception('failed to recover container %r', rt_uuid)
        else:
            _log.debug('recovered container %r', rt_uuid)
    return doms.get_all()


def openConnection(uri, repo=None):
    if uri != 'convirt:///system':
        errors.throw()  # TODO: more specific error?
    repo = command.Repo() if repo is None else repo
    return connection.Connection(repo)


def openAuth(uri, auth, flags=0):
    return openConnection(uri)


def openReadOnly(uri):
    errors.throw()  # TODO: more specific error?
