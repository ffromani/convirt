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

from .. import command
from .. import runner
from . import ContainerRuntime


class Fake(ContainerRuntime):

    _log = logging.getLogger('convirt.runtime.Fake')

    NAME = 'fake'

    _PREFIX = 'fake-'

    def __init__(self,
                 conf,
                 repo,
                 rt_uuid=None):
        super(Fake, self).__init__(conf, repo, rt_uuid)
        self._log.debug('fake runtime %s', self._uuid)
        self._running = False
        self._actions = {
            'start': 0,
            'stop': 0,
            'resync': 0,
        }

    @property
    def actions(self):
        return self._actions.copy()

    @staticmethod
    def available():
        return True

    @classmethod
    def configure_runtime(cls):
        pass  # TODO

    @property
    def running(self):
        return self._running

    def start(self, target=None):
        if self.running:
            raise runner.OperationFailed('already running')

        self._actions['start'] += 1
        self._running = True

    def stop(self):
        if not self.running:
            raise runner.OperationFailed('not running')

        self._actions['stop'] += 1
        self._running = False

    def resync(self):
        self._actions['resync'] += 1
