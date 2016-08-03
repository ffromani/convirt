#
# Copyright 2016 Red Hat, Inc.
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

import importlib
import logging
import pkgutil
import threading

from . import runtimes


_lock = threading.Lock()
_rts = {}
_ready = False


def _register():
    global _rts
    if not _rts:
        rts = {}
        for _, module_name, _ in pkgutil.iter_modules([runtimes.__path__[0]]):
            module = importlib.import_module(
                '%s.%s' % (runtimes.__name__, module_name)
            )
            if hasattr(module, 'register'):
                rts.update(module.register())
        _rts = rts
    return _rts


def _unregister():
    global _rts
    _rts.clear()


class Unsupported(Exception):
    """
    TODO
    """


class SetupError(Exception):
    pass


_log = logging.getLogger('convirt.runtime')


def create(rt, conf, repo, **kwargs):
    global _lock
    global _rts

    with _lock:
        klass = _rts.get(rt, None)

    if klass is None:
        raise Unsupported(rt)

    _log.debug('creating container with runtime %r', klass.NAME)
    return klass(conf, repo, **kwargs)


# FIXME: testing (half-hack)
def supported(register=True):
    global _lock
    global _rts
    with _lock:
        if register:
            _register()
        return frozenset(list(_rts.keys()))


def setup():
    global _lock
    global _ready
    global _rts
    with _lock:
        if _ready:
            raise SetupError('setup already done')
        _register()
        for name, rt in list(_rts.items()):
            _log.debug('setting up runtime %r', name)
            rt.setup_runtime()
        _ready = True


def teardown():
    global _lock
    global _ready
    global _rts
    with _lock:
        if not _ready:
            raise SetupError('teardown already done')
        for name, rt in list(_rts.items()):
            _log.debug('shutting down runtime %r', name)
            rt.teardown_runtime()
        _unregister()
        _ready = False


def configure():
    global _lock
    global _rts
    with _lock:
        _register()
        for name, rt in list(_rts.items()):
            _log.debug('configuring runtime %r', name)
            rt.configure_runtime()


# for test purposes
def clear():
    global _ready
    global _rts
    with _lock:
        _unregister()
        _ready = False
