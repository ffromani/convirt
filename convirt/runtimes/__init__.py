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

import collections
import logging
import uuid

from .. import command
from .. import runner


# TODO: networking
RunConfig = collections.namedtuple(
    'RunConfig', ['image_path', 'memory_size_mib', 'network'])


class ConfigError(Exception):
    """
    TODO
    """


_NULL = command.Path('false', paths=tuple())


class ContainerRuntime(object):

    _log = logging.getLogger('convirt.runtime.Base')

    NAME = ''

    _PATH = _NULL

    @classmethod
    def available(cls):
        return cls._PATH.cmd is not None

    def __init__(self, conf, rt_uuid=None):
        self._conf = conf
        self._uuid = (
            uuid.uuid4() if rt_uuid is None else
            uuid.UUID(rt_uuid)
        )
        self._run_conf = None
        self._runner = runner.Runner(self.unit_name())
        self._runner.configure(self._conf)

    @property
    def uuid(self):
        return str(self._uuid)

    def unit_name(self):
        return "%s%s" % (runner.PREFIX, self.uuid)

    def configure(self, xml_tree):
        self._log.debug('configuring runtime %r', self.uuid)
        mem = self._find_memory(xml_tree)
        path = self._find_image(xml_tree)
        try:
            net = self._find_network(xml_tree)
        except ConfigError:
            if self._conf.net_fallback:
                self._log.debug('no network detected for %r, using default',
                                self.uuid)
                net = None
            else:
                raise
        self._run_conf = RunConfig(path, mem, net)
        self._log.debug('configured runtime %s: %s',
                        self.uuid, self._run_conf)

    def start(self, target=None):
        raise NotImplementedError

    def resync(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

    def runtime_name(self):
        raise NotImplementedError

    def setup(self):
        pass  # optional

    def teardown(self):
        pass  # optional

    @classmethod
    def setup_runtime(cls):
        pass  # optional

    @classmethod
    def teardown_runtime(cls):
        pass  # optional

    @classmethod
    def configure_runtime(cls):
        pass  # optional

    @property
    def runtime_config(self):
        """
        Shortcut for test purposes only. May be removed in future versions.
        """
        return self._run_conf

    def _find_memory(self, xml_tree):
        mem_node = xml_tree.find('./maxMemory')
        if mem_node is not None:
            mem = int(mem_node.text)/1024
            self._log.debug('runtime %r found memory = %i MiB',
                            self.uuid, mem)
            return mem
        raise ConfigError('memory')

    def _find_image(self, xml_tree):
        disks = xml_tree.findall('.//disk[@type="file"]')
        for disk in disks:
            # TODO: add in the findall() above?
            device = disk.get('device')
            if device != 'disk':
                continue
            source = disk.find('./source/[@file]')
            if source is None:
                continue
            image_path = source.get('file')
            self._log.debug('runtime %r found image path %r',
                            self.uuid, image_path)
            return image_path.strip('"')
        raise ConfigError('image path not found')

    def _find_network(self, xml_tree):
        interfaces = xml_tree.findall('.//interface[@type="bridge"]')
        for interface in interfaces:
            link = interface.find('./link')
            if link.get('state') != 'up':
                continue
            source = interface.find('./source[@bridge]')
            if source is None:
                continue
            bridge = source.get('bridge')
            self._log.debug('runtime %r found bridge %r', self.uuid, bridge)
            return bridge.strip('"')
        raise ConfigError('network settings not found')  # TODO
