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

import collections
import json
import logging
import os
import os.path
import time

from .config import network
from . import command
from . import runner
from . import runtime


_MACHINECTL = command.Path('machinectl')
_RKT = command.Path('rkt')


class Rkt(runtime.Base):

    _log = logging.getLogger('convirt.runtime.Rkt')

    NAME = 'rkt'

    _PREFIX = 'rkt-'

    _RKT_UUID_FILE = 'rkt_uuid'

    _PATH = _RKT

    _TRIES = 10  # TODO: make config item?

    _DELAY = 1  # seconds  TODO: make config item?

    def __init__(self, conf, rt_uuid=None):
        super(Rkt, self).__init__(conf, rt_uuid)
        rkt_uuid_file = '%s.%s' % (self._uuid, self.NAME)
        self._rkt_uuid_path = os.path.join(
            self._conf.run_dir, rkt_uuid_file)
        self._log.debug('rkt runtime %s uuid_path=[%s]',
                        self._uuid, self._rkt_uuid_path)
        self._rkt_uuid = None

    @classmethod
    def configure_runtime(cls):
        conf = network.current()
        with Network() as net:
            net.update(conf)

    @property
    def running(self):
        return self._rkt_uuid is not None

    def start(self, target=None):
        if self.running:
            raise runner.OperationFailed('already running')

        cmd = self.command_line(target)
        runtime.rm_file(self._rkt_uuid_path)
        self._runner.start(cmd)
        self.resync()

    def resync(self):
        self._collect_rkt_uuid(self._rkt_uuid_path)

    def stop(self):
        if not self.running:
            raise runner.OperationFailed('not running')

        cmd = [
            _MACHINECTL.cmd(),
            'poweroff',
            self.runtime_name(),
        ]
        self._runner.call(cmd)
        try:
            os.remove(self._rkt_uuid_path)
        except OSError:
            pass  # TODO
        self._rkt_uuid = None

    def command_line(self, target=None):
        image = self._run_conf.image_path if target is None else target
        network = (
            'default'
            if self._run_conf.network is None else
            self._run_conf.network
        )
        cmd = [
            Rkt._PATH.cmd(),
            '--uuid-file-save=%s' % self._rkt_uuid_path,
            '--insecure-options=image',  # FIXME
#            '--net=%s' % network,
            'run',
            '%s' % image,
            '--memory=%iM' % (self._run_conf.memory_size_mib),
        ]
        return cmd

    def runtime_name(self):
        if self._rkt_uuid is None:
            return None
        return '%s%s' % (self._PREFIX, self._rkt_uuid)

    def _collect_rkt_uuid(self, path):
        for i in range(self._TRIES):
            try:
                self._read_rkt_uuid(path)
            except IOError:
                self._log.debug('rkt runtime read UUID: try %i/%i failed',
                                i+1, self._TRIES)
                time.sleep(self._DELAY)
            else:
                self._log.info('read rkt UUID at try %i/%i',
                                i+1, self._TRIES)
                return
        raise runner.OperationFailed('failed to read rkt UUID')

    def _read_rkt_uuid(self, path):
        with open(path, 'rt') as f:
            self._rkt_uuid = f.read().strip()
            self._log.info('rkt container %s rkt_uuid %s',
                            self._uuid, self._rkt_uuid)


class Network(object):

    DIR = '/etc/rkt/net.d'

    NAME = '50-convirt-containers.conf'

    _log = logging.getLogger('convirt.runtime.Rkt')

    def __init__(self, name=None):
        self._name = self.NAME if name is None else name
        self._data = {}
        self._dirty = False

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.save()

    def __eq__(self, other):
        return self._data == other._data

    @property
    def path(self):
        return os.path.join(self.DIR, self._name)

    def update(self, conf):
        new_data = self._make(conf)
        if self._data != new_data:
            self._data = new_data
            self._dirty = True

    def load(self):
        try:
            with open(self.path, 'rt') as src:
                self._data = json.load(src)
        except IOError:
            self._log.debug('config: cannot load %r, ignored', self.path)
        return self._data

    def save(self, force=False):
        if not self._dirty and not force:
            self._log.info('config: no update needed, save skipped')
        else:
            with open(self.path, 'wt') as dst:
                json.dump(self._data, dst)

    def clear(self):
        runtime.rm_file(self.path)

    # test/debug purposes
    def get_conf(self):
        net, mask = self._data["ipam"]["subnet"].split('/')
        return {
            "bridge": self._data["bridge"],
            "subnet": net,
            "mask": int(mask),
        }

    def _make(self, conf):
        bridge = conf["bridge"]
        self._log.debug('config: using bridge %r', bridge)
        return {
            "name": "containers",
            "type": "bridge",
            "bridge": bridge,
            "ipam": self._make_ipam(conf)
        }

    def _make_ipam(self, conf):
        subnet = "%s/%s" % (conf["subnet"], conf["mask"])
        self._log.debug('config: using subnet %r', subnet)
        return {
            "type": "host-local",
            "subnet": subnet,
        }
