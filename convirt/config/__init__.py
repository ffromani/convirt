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

    def __repr__(self):
        return repr(self.__dict__)


__all__ = ['environ', 'network']
