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


docker = command.Path('docker')


command.executables['docker'] = docker


_TEMPLATES = {
    'docker_run':
        'run '
        '--name=${unit_name} '
        '${image}',

}


class Docker(ContainerRuntime):

    _log = logging.getLogger('convirt.runtime.Docker')

    NAME = 'docker'

    _PREFIX = 'dkr-'

    def __init__(self,
                 conf,
                 repo,
                 rt_uuid=None):
        super(Docker, self).__init__(conf, repo, rt_uuid)
        self._log.debug('docker runtime %s', self._uuid)
        self._running = False
        self._docker_run = self._runner.repo.get(
            'docker', _TEMPLATES['docker_run'],
            unit_name=self.unit_name(),
        )

    @staticmethod
    def available():
        return docker.available

    @classmethod
    def configure_runtime(cls):
        pass  # TODO

    @property
    def running(self):
        return self._runner.running

    def start(self, target=None):
        if self.running:
            raise runner.OperationFailed('already running')

        self._runner.start(
            command=self._docker_run,
            image=self._run_conf.image_path if target is None else target,
        )

    def stop(self):
        if not self.running:
            raise runner.OperationFailed('not running')

        self._runner.stop()
