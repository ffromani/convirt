#
# Copyright 2008-2016 Red Hat, Inc.
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
import shlex
import subprocess
import string


class NotFound(Exception):
    pass


class Path(object):
    def __init__(self, name, paths=None):
        self._name = name
        self._paths = paths
        self._cmd = None

    @property
    def name(self):
        return self._name

    @property
    def paths(self):
        if self._paths is None:
            self._paths = self._find_paths()
        return self._paths

    @property
    def cmd(self):
        try:
            return self.get()
        except NotFound:
            return None

    def get(self):
        if self._cmd is None:
            self._cmd = self._which(self._name)
        if self._cmd is None:
            raise NotFound(self._name)
        return self._cmd

    def _find_paths(self):
        try:
            paths = os.environ['PATH']
        except KeyError:
            paths = ''
        return paths.split(':')

    def _which(self, name):
        for path in self.paths:
            cmd = os.path.join(path, self._name)
            if os.access(cmd, os.X_OK):
                return cmd
        return None


systemctl = Path('systemctl')
systemd_run = Path('systemd-run')
machinectl = Path('machinectl')


# TODO document the purpose
executables = [
    systemctl,
    systemd_run,
    machinectl,
]


class Failed(Exception):
    """
    command failed to execute
    """


class NotAllowed(Exception):
    """
    command not allowed to run
    """


class Command(object):

    _log = logging.getLogger('command')

    @classmethod
    def from_name(cls, name, template):
        obj = cls(Path(name), template)
        return obj

    def __init__(self, path, template, **kwargs):
        self.ident = '*'
        self._path = path
        tmpl = string.Template(template)
        self._template = string.Template(tmpl.safe_substitute(**kwargs))

    @property
    def path(self):
        return self._path.cmd

    def argv(self, **kwargs):
        return self.path + ' ' + self._template.substitute(**kwargs)

    def cmdline(self, **kwargs):
        args = {}
        for key, val in kwargs.items():
            if isinstance(val, Command):
                ctx = kwargs.copy()
                ctx.pop(key)
                val = val.argv(**ctx)
            args[key] = val
        optstr = self.argv(**args)
        return shlex.split(optstr)

    def __call__(self, **kwargs):
        cmd = self.cmdline(**kwargs)
        if not self.allowed(cmd):
            raise NotAllowed(cmd)
        return self._execute(cmd)

    def allowed(self, argv):
        return True

    def _execute(self, argv):
        raise NotImplementedError


class FakeCommand(Command):
    def _execute(self, argv):
        self._log.info('faking call: %r', argv)
        return ' '.join(argv)


class SubProcCommand(Command):
    def _execute(self, argv):
        self._log.debug('%s calling %r',
                        self.ident, argv)
        try:
            return subprocess.check_output(cmd)
        except subprocess.CalledProcessError as exc:
            raise Failed(str(exc))
        finally:
            log.debug('%s called %r',
                      self.ident, argv)
