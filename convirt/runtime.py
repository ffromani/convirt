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

import collections
import os.path
import subprocess

from . import command
from . import config


_NULL = command.Path('false', paths=tuple())
_SUDO = command.Path('sudo')
_SYSTEMCTL = command.Path('systemctl')
_SYSTEMD_CGTOP = command.Path('systemd-cgtop')
_SYSTEMD_RUN = command.Path('systemd-run')

_PREFIX = 'convirt-'
_SERVICE_EXT = ".service"


class OperationFailed(Exception):
    """
    TODO
    """

CGStat = collections.namedtuple('CGStat',
                                ['path', 'tasks', 'cpu_percentage',
                                 'memory', 'input_per_sec', 'output_per_sec'])


def get_all():
    cmd = [
        _SYSTEMCTL.cmd(),
        'list-units',
        '--no-pager',
        '--no-legend',
        '%s*' % _PREFIX,
    ]
    output = subprocess.check_output(cmd)
    for item in _parse_systemctl_list_units(output):
        yield item


class Base(object):

    _PATH = _NULL

    @classmethod
    def available(cls):
        try:
            return cls._PATH.cmd() is not None
        except command.NotFound:
            return False

    def __init__(self, vm_uuid, base_dir):
        self._vm_uuid = vm_uuid
        self._base_dir = base_dir
        self._conf = config.current()

    def configure(self, xml_tree):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        cmd = [
            _SYSTEMCTL.cmd(),
            'stop',
            self._unit_name(),
        ]
        self._exec(cmd)

    def run(self, *args):
        cmd = [
            _SYSTEMD_RUN.cmd(),
            '--unit="%s"' % self._unit_name(),
            '--uid=%i' % self._conf.uid,
            '--gid=%i' % self._conf.gid,
        ]
        cmd.extend(*args)
        self._exec(cmd)

    @staticmethod
    def stats():
        output = str(subprocess.check_output([
            _SYSTEMD_CGTOP.cmd(),
        ]))
        for stat in _parse_systemd_cgtop(output):
            yield stat

    def _unit_name(self):
        return "%s%s" % (_PREFIX, self._vm_uuid)

    def _exec(self, cmd):
        command = [_SUDO.cmd() if self._conf.use_sudo else []]
        command.extend(cmd)
        rc = subprocess.check_call(command)
        if rc != 0:
            raise OperationFailed()


def _parse_systemd_cgtop(output):
    for line in output.splitlines():
        if _PREFIX in line:
            yield CGStat(*line.split())


def _parse_systemctl_list_units(output):
    for line in output.splitlines():
        if not line:
            continue
        unit = line.split()[0]
        name, ext = os.path.splitext(unit)
        if ext != _SERVICE_EXT:  # TODO: check this
            continue
        yield name.replace(_PREFIX, '', 1)
