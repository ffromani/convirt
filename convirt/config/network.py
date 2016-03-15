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

from . import AttrDict

# alias for nicer (?) name
Network = AttrDict


# TODO: remove duplication


_NET = Network(
    bridge='convirt',
    subnet='10.1.0.0',
    mask='16',
)


def current():
    net = Network()
    net.update(_NET)
    return net


def setup(net):
    global _NET
    new_NET = Network((k, v) for k, v in list(_NET.items()))
    new_NET.update(net)
    _NET = new_NET


def update(**kwargs):
    global _NET
    new_NET = Network((k, v) for k, v in list(_NET.items()))
    new_NET.update(kwargs)
    _NET = new_NET
    return new_NET
