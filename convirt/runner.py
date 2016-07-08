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
import os
import os.path

from . import command
from . import config


PREFIX = 'convirt-'
_SERVICE_EXT = ".service"


_TEMPLATES = {
    'systemd-run':
        '--unit=${unit} '
        '--slice=${slice} '
        '--property=CPUAccounting=1 '
        '--property=MemoryAccounting=1 '
        '--property=BlockIOAccounting=1 '
        '${command}',

    'machinectl_poweroff':
        'poweroff '
        '${name}',

    'systemctl_stop':
        'stop '
        '${name}',

    'systemctl_list':
        'list-units '
        '--no-pager '
        '--no-legend '
        '${prefix}*',
}


class OperationFailed(Exception):
    """
    WRITEME
    """


class Runner(object):

    _log = logging.getLogger('convirt.runner')

    def __init__(self, unit_name, repo):
        self._unit_name = unit_name
        self._repo = repo
        self._conf = config.environ.current()
        self._running = False
        self._machinectl_poweroff = self._repo.get(
            'machinectl', _TEMPLATES['machinectl_poweroff'],
        )
        self._systemctl_stop = self._repo.get(
            'systemctl', _TEMPLATES['systemctl_stop'],
        )
        self._systemd_run = self._repo.get(
            'systemd-run', _TEMPLATES['systemd-run'],
            unit=self._unit_name,
            slice=self._conf.cgroup_slice,
        )

    @property
    def repo(self):
        return self._repo

    @property
    def running(self):
        return self._running

    def configure(self, conf):
        self._conf = conf

    def stop(self, runtime_name=None):
        if runtime_name is None:
            self._systemctl_stop(name=self._unit_name)
        else:
            self._machinectl_poweroff(name=runtime_name)
        self._running = False

    def start(self, **kwargs):
        self._systemd_run(**kwargs)
        self._running = True

    def get_pid(self):
        if not self._running:
            raise OperationFailed("not yet started")
        return 0

    @classmethod
    def stats(cls):
        return []

    @classmethod
    def get_all(cls, repo=None):
        repo = command.Repo() if repo is None else repo
        systemctl_list = repo.get(
            'systemctl', _TEMPLATES['systemctl_list'],
        )
        output = systemctl_list(prefix=PREFIX)
        for item in _parse_systemctl_list_units(output):
            yield item


def _vm_uuid_from_unit(unit):
    name, ext = os.path.splitext(unit)
    if ext != _SERVICE_EXT:  # TODO: check this
        raise ValueError(unit)
    return name.replace(PREFIX, '', 1)


def _parse_systemctl_list_units(output):
    for line in output.splitlines():
        if not line:
            continue
        try:
            unit, loaded, active, sub, desc = line.split(None, 4)
        except ValueError:
            logging.warning('unexpected systemctl line: %r', line)
            continue
        if not _is_running_unit(loaded, active, sub):
            continue
        try:
            yield _vm_uuid_from_unit(unit)
        except ValueError:
            pass


def _is_running_unit(loaded, active, sub):
    return (
        loaded == 'loaded' and
        active == 'active' and
        sub == 'running'
    )
