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

import logging
import os
import os.path
import subprocess

from . import command
from . import config


PREFIX = 'convirt-'
_SERVICE_EXT = ".service"

_SUDO = command.Path('sudo')
_SYSTEMCTL = command.Path('systemctl')
_SYSTEMD_RUN = command.Path('systemd-run')


class OperationFailed(Exception):
    """
    TODO
    """


class Runner(object):

    _log = logging.getLogger('convirt.runtime.Runner')

    def __init__(self, unit_name, conf=None):
        self._unit_name = unit_name
        self._conf = config.current() if conf is None else conf
        self._running = False

    @property
    def running(self):
        return self._running

    def stop(self):
        cmd = [
            _SYSTEMCTL.cmd(),
            'stop',
            self._unit_name,
        ]
        self.call(cmd)
        self._running = False

    def start(self, *args):
        cmd = self.command_line()
        cmd.extend(*args)
        self.call(cmd)
        self._running = True

    @staticmethod
    def stats():
        return []  # TODO

    def command_line(self):
        cmd = [_SYSTEMD_RUN.cmd()]
        if self._unit_name is not None:
            cmd.append('--unit=%s' % self._unit_name)
        cmd.extend([
            '--slice=%s' % self._conf.cgroup_slice,
            '--property=CPUAccounting=1',
            '--property=MemoryAccounting=1',
            '--property=BlockIOAccounting=1',
        ])
        if self._conf.uid is not None:
            cmd.append('--uid=%i' % self._conf.uid)
        if self._conf.gid is not None:
            cmd.append('--gid=%i' % self._conf.gid)
        return cmd

    def call(self, cmd):
        command = []
        if self._conf.use_sudo:
            command.append(_SUDO.cmd())
        command.extend(cmd)
        self._log.debug('%s about to call [%s]', self._unit_name, cmd)
        rc = subprocess.check_call(command)
        self._log.debug('%s called [%s] rc=%i', self._unit_name, cmd, rc)
        if rc != 0:
            raise OperationFailed()


def get_all():
    cmd = [
        _SYSTEMCTL.cmd(),
        'list-units',
        '--no-pager',
        '--no-legend',
        '%s*' % PREFIX,
    ]
    output = subprocess.check_output(cmd)
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
