from __future__ import absolute_import
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

from collections import MutableMapping

# http://code.activestate.com/recipes/576972-attrdict/
class AttrDict(MutableMapping):

    """Dict-like object that can be accessed by attributes

    >>> obj = AttrDict()
    >>> obj['test'] = 'hi'
    >>> print obj.test
    hi
    >>> del obj.test
    >>> obj.test = 'bye'
    >>> print obj['test']
    bye
    >>> print len(obj)
    1
    >>> obj.clear()
    >>> print len(obj)
    0
    """

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __setitem__(self, key, val):
        self.__setattr__(key, val)

    def __delitem__(self, key):
        self.__delattr__(key)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


# alias for nicer (?) name
Environment = AttrDict


# NOTE about run_dir:
# we used to want
# /base/dir/
#         +- $UUID/
#                +- rkt_uuid
#
# Actually, we don't need this subdir, so we switched
# to the simpler schema.
#
# /base/dir/
#         +- $UUID.rkt
#
# for the time being

_ENV = Environment(
    uid=None,
    gid=None,
    tools_dir='/usr/libexec/convirt',
    run_dir='/run/convirt',
    use_sudo=True,
    cgroup_slice='convirt',  # XXX: or 'machine' ?
)


def current():
    env = Environment()
    env.update(_ENV)
    return env


def setup(env):
    global _ENV
    new_ENV = Environment((k, v) for k, v in list(_ENV.items()))
    new_ENV.update(env)
    _ENV = new_ENV


def update(**kwargs):
    global _ENV
    new_ENV = Environment((k, v) for k, v in list(_ENV.items()))
    new_ENV.update(kwargs)
    _ENV = new_ENV
    return new_ENV
