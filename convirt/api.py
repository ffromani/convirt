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

import logging
import threading

from . import rkt
from . import runtime


_log = logging.getLogger('convirt')

_lock = threading.Lock()
_runtimes = {}
_ready = False


class APIError(Exception):
    pass


def _available():
    with _lock:
        _register()
    return _runtimes


def supported():
    runtimes = _available()
    return frozenset(list(runtimes.keys()))


def setup(register=False):
    global _ready
    global _runtimes
    with _lock:
        if _ready:
            raise APIError('setup already done')
        if register:
            _register()
        for name, rt in _runtimes.items():
            _log.debug('setting up runtime %r', name)
            rt.setup_runtime()
        _ready = True


def teardown(clear=False):
    global _ready
    global _runtimes
    with _lock:
        if not _ready:
            raise APIError('teardown already done')
        for name, rt in _runtimes.items():
            _log.debug('shutting down runtime %r', name)
            rt.teardown_runtime()
        if clear:
            _runtimes.clear()
        _ready = False


def create(rt, *args, **kwargs):
    runtimes = _available()
    if rt in runtimes:
        _log.debug('creating container with runtime %r', rt)
        return runtimes[rt](*args, **kwargs)
    raise runtime.Unsupported(rt)


# for test purposes
def clear():
    global _ready
    global _runtimes
    with _lock:
        _runtimes.clear()
        _ready = False


def _find_runtimes():
    rts = {}
    if rkt.Rkt.available():
        rts[rkt.Rkt.NAME] = rkt.Rkt
    return rts


def _register():
    global _runtimes
    if not _runtimes:
        _runtimes = _find_runtimes()
