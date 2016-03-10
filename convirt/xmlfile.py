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
import os.path
import xml.etree.ElementTree as ET

import six

from . import runtime


class UnconfiguredXML(Exception):
    """
    XML configuration missing
    """


class XMLFile(object):

    _log = logging.getLogger('convirt.XMLFile')

    @staticmethod
    def encode(root):
        encoding = 'unicode' if six.PY3 else 'utf-8'
        return ET.tostring(root, encoding=encoding)

    def __init__(self, name, conf):
        self._name = name
        self._conf = conf
        if self._conf is None:
            raise UnconfiguredXML(self._name)

    @property
    def path(self):
        return os.path.join(
            self._conf.run_dir, '%s.xml' % (self._name)
        )

    def load(self):
        return ET.fromstring(self.read())

    def read(self):
        self._log.debug('loading cached XML %r', self._name)
        with open(self.path, 'rt') as src:
            return src.read()

    def save(self, root):
        self._log.debug('saving cached XML %r', self._name)
        with open(self.path, 'wt') as dst:
            dst.write(XMLFile.encode(root))

    def clear(self):
        self._log.debug('clearing cached XML for container %s', self._name)
        runtime.rm_file(self.path)
