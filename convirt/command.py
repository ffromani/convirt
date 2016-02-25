from __future__ import absolute_import
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

import os
import os.path


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

    def cmd(self):
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
