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
import logging
import os
import os.path

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

    def __init__(self, vm_uuid, conf=None):
        super(Rkt, self).__init__(vm_uuid, conf)
        rkt_uuid_file = '%s.%s' % (self._vm_uuid, self.NAME)
        self._rkt_uuid_path = os.path.join(
            self._conf.run_dir, rkt_uuid_file)
        self._log.debug('rkt container %s uuid_path=[%s]',
                        self._vm_uuid, self._rkt_uuid_path)
        self._rkt_uuid = None

    @property
    def running(self):
        return self._rkt_uuid is not None

    def start(self, target=None):
        if self.running:
            raise runner.OperationFailed('already running')

        image = self._run_conf.image_path if target is None else target
        cmd = [
            Rkt._PATH.cmd(),
            '--uuid-file-save="%s"' % self._rkt_uuid_path,
            '--insecure-options=image',  # FIXME
            'run',
            '--memory=%iM' % (self._run_conf.memory_size_mib),
            '%r' % image,
        ]
        self._runner.start(cmd)
        with open(self._rkt_uuid_path, 'rt') as f:
            self._rkt_uuid = f.read().strip()
            self._log.info('rkt container %s rkt_uuid %s',
                            self._vm_uuid, self._rkt_uuid)

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
    
    def runtime_name(self):
        if self._rkt_uuid is None:
            return None
        return '%s%s' % (self._PREFIX, self._rkt_uuid)
