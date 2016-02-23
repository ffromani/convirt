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

# TODO: logging
import collections
import os.path
import subprocess

from . import command
from . import config


_NULL = command.Path('false', paths=tuple())
_SUDO = command.Path('sudo')
_SYSTEMCTL = command.Path('systemctl')
_SYSTEMD_RUN = command.Path('systemd-run')

_PREFIX = 'convirt-'
_SERVICE_EXT = ".service"


class Unsupported(Exception):
    """
    TODO
    """


class OperationFailed(Exception):
    """
    TODO
    """


class ConfigError(Exception):
    """
    TODO
    """


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


class Runner(object):

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
        cmd = [
            _SYSTEMD_RUN.cmd(),
            '--unit="%s"' % self._unit_name,
            '--slice=%s' % self._conf.cgroup_slice,
            '--property=CPUAccounting=1',
            '--property=MemoryAccounting=1',
            '--property=BlockIOAccounting=1',
        ]
        if self._conf.uid is not None:
            cmd.append('--uid=%i' % self._conf.uid)
        if self._conf.gid is not None:
            cmd.append('--gid=%i' % self._conf.gid)
        cmd.extend(*args)
        self.call(cmd)
        self._running = True

    @staticmethod
    def stats():
        return []  # TODO

    def call(self, cmd):
        command = []
        if self._conf.use_sudo:
            command.append(_SUDO.cmd())
        command.extend(cmd)
        rc = subprocess.check_call(command)
        if rc != 0:
            raise OperationFailed()


# TODO: networking
RunConfig = collections.namedtuple('RunConfig',
                                   ['image_path', 'memory_size_mib'])


class Base(object):

    NAME = ''

    _PATH = _NULL

    @classmethod
    def available(cls):
        try:
            return cls._PATH.cmd() is not None
        except command.NotFound:
            return False

    def __init__(self, vm_uuid, conf=None):
        self._vm_uuid = vm_uuid
        self._conf = config.current() if conf is None else conf
        self._run_conf = None
        self._run_dir = os.path.join(self._conf.run_dir, self._vm_uuid)
        self._runner = Runner(self.unit_name(), self._conf)

    def unit_name(self):
        return "%s%s" % (_PREFIX, self._vm_uuid)

    def setup(self):
        os.mkdir(self._run_dir, 0o750)

    def teardown(self):
        os.rmdir(self._run_dir)

    def configure(self, xml_tree):
        mem = self._find_memory(xml_tree)
        path = self._find_image(xml_tree)
        # TODO: network
        self._run_conf = RunConfig(path, mem)

    def start(self, target=None):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

    def runtime_name(self):
        raise NotImplementedError

    @property
    def runtime_config(self):
        """
        Shortcut for test purposes only. May be removed in future versions.
        """
        return self._run_conf

    def _find_memory(self, xml_tree):
        mem_node = xml_tree.find('./maxMemory')
        if mem_node is not None:
            return int(mem_node.text)/1024
        raise ConfigError('memory')

    def _find_image(self, xml_tree):
        disks = xml_tree.findall('.//disk[@type="file"]')
        for disk in disks:
            source = disk.find('./source/[@file]')
            if source is not None:
                return source.get('file')
        raise ConfigError('image path')


def _vm_uuid_from_unit(unit):
    name, ext = os.path.splitext(unit)
    if ext != _SERVICE_EXT:  # TODO: check this
        raise ValueError(unit)
    return name.replace(_PREFIX, '', 1)


def _parse_systemctl_list_units(output):
    for line in output.splitlines():
        if not line:
            continue
        unit = line.split()[0]
        try:
            yield _vm_uuid_from_unit(unit)
        except ValueError:
            pass
