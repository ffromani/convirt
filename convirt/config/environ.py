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
    cleanup_expire_period=3600,  # seconds
    cleanup_grace_period=30,  # seconds
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
