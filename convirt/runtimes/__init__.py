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
from .. import xmlfile


# TODO: networking
RunConfig = collections.namedtuple(
    'RunConfig', ['image_path', 'volume_paths', 'volume_mapping',
                  'memory_size_mib', 'network'])


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

    def __init__(self,
                 conf,
                 runr=runner.Subproc.create,
                 rt_uuid=None):
        self._conf = conf
        self._uuid = (
            uuid.uuid4() if rt_uuid is None else
            uuid.UUID(rt_uuid)
        )
        self._run_conf = None
        self._runner = runr(self.unit_name())
        self._runner.configure(self._conf)

    @property
    def uuid(self):
        return str(self._uuid)

    def unit_name(self):
        return "%s%s" % (runner.PREFIX, self.uuid)

    def configure(self, xml_tree):
        self._log.debug('configuring runtime %r', self.uuid)
        dom = DomainParser(xml_tree, self._uuid, self._log)
        mem = dom.memory()
        path, volumes = dom.drives()
        mapping = dom.drives_map()
        net = dom.network()
        self._run_conf = RunConfig(path, volumes, mapping, mem, net)
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


class DomainParser(object):

    def __init__(self, xml_tree, uuid, log):
        self._xml_tree = xml_tree
        self._uuid = uuid
        self._log = log

    @property
    def uuid(self):
        return self._uuid

    def memory(self):
        mem_node = self._xml_tree.find('./maxMemory')
        if mem_node is not None:
            mem = int(mem_node.text)/1024
            self._log.debug('runtime %r found memory = %i MiB',
                            self.uuid, mem)
            return mem
        raise ConfigError('memory')

    def drives(self):
        images, volumes = [], []
        disks = self._xml_tree.findall('.//disk[@type="file"]')
        for disk in disks:
            # TODO: add in the findall() above?
            device = disk.get('device')
            if device == 'cdrom':
                target = images
            elif device == 'disk':
                target = volumes
            else:
                continue
            source = disk.find('./source/[@file]')
            if source is None:
                continue
            image_path = source.get('file')
            self._log.debug('runtime %r found image path %r',
                            self.uuid, image_path)
            target.append(image_path.strip('"'))
        image = self._find_image(images)
        return image, volumes

    def drives_map(self):
        mapping = {}
        entries = self._xml_tree.findall(
            './metadata/{%s}drivemap/volume' % xmlfile.CONVIRT_DRIVEMAP_URI,
        )
        for entry in entries:
            name = entry.get('name')
            drive = entry.get('drive')
            mapping[name] = drive
        return mapping

    def network(self):
        interfaces = self._xml_tree.findall('.//interface[@type="bridge"]')
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

    def _find_image(self, images):
        if not images:
            raise ConfigError('image path not found')
        if len(images) > 1:
            self._log.warning(
                'found more than one image: %r, using the first one',
                images)
        image = self._override_image()
        if image is None:
            image = images[0]
        return image

    def _override_image(self):
        cont = self._xml_tree.find(
            './metadata/{%s}container' % xmlfile.CONVIRT_URI
        )
        if cont is None:
            return None
        return cont.get('image')
