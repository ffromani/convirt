from __future__ import absolute_import
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

# TODO: this module has an ugly name. Suggestions welcome!
# discarded alternatives:
# dommap/dom_map - ugly as well
# container - ugly, misleading
# domcontainer - as above
# domcont* - (any abbreviation I could think of) as above


import threading


_lock = threading.Lock()
_doms = {}


def get_all():
    with _lock:
        return list(_doms.values())  # py3 compat


def get_by_uuid(vm_uuid):
    with _lock:
        return _doms[str(vm_uuid)]


def add(dom):
    with _lock:
        _doms[dom.UUIDString()] = dom


def remove(vm_uuid):
    with _lock:
        del _doms[vm_uuid]


# use only for testing
def clear():
    with _lock:
        _doms.clear()
