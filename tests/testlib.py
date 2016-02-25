#
# Copyright 2015-2016 Red Hat, Inc.
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

from contextlib import contextmanager
import shutil
import tempfile
import unittest

import convirt.config


class TestCase(unittest.TestCase):
    def assertNotRaises(self, callableObj=None, *args, **kwargs):
        # This is required when any exception raised during the call should be
        # considered as a test failure.
        context = not_raises(self)
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)


@contextmanager
def not_raises(test_case):
    try:
        yield
    except Exception as e:
        raise test_case.failureException("Exception raised: %s" % e)


class TruePath(object):
    def cmd(self):
        return True


class NonePath(object):
    def cmd(self):
        return None


TEMPDIR = '/tmp'


@contextmanager
def named_temp_dir(base=TEMPDIR):
    tmp_dir = tempfile.mkdtemp(dir=base)
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir)


def make_conf(**kwargs):
    conf = convirt.config.current()
    conf.use_sudo = False  # hack for convenience
    for k, v in kwargs.items():
        setattr(conf, k, v)
    return conf


@contextmanager
def global_conf(**kwargs):
    saved_conf = convirt.config.current()

    conf = make_conf(**kwargs)
    convirt.config.setup(conf)
    try:
        yield conf
    finally:
        convirt.config.setup(saved_conf)
