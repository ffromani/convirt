from __future__ import absolute_import
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
import uuid
import unittest

import convirt.api
import convirt.command
import convirt.config

from . import monkey


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
    for k, v in list(kwargs.items()):
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


class RunnableTestCase(TestCase):

    def setUp(self):
        self.guid = uuid.uuid4()
        self.run_dir = tempfile.mkdtemp()
        paths = ['.', './tests']
        fake_mctl = convirt.command.Path('true')
        fake_rkt = convirt.command.Path('fake-rkt', paths=paths)
        fake_sdrun = convirt.command.Path('fake-systemd-run', paths=paths)
        self.patch = monkey.Patch([
            (convirt.rkt.Rkt, '_PATH', fake_rkt),
            (convirt.rkt, '_MACHINECTL', fake_mctl),
            (convirt.runner, '_SYSTEMD_RUN', fake_sdrun)])
        self.patch.apply()

    def tearDown(self):
        self.patch.revert()
        shutil.rmtree(self.run_dir)


class FakeRunnableTestCase(TestCase):

    def setUp(self):
        self.runners = []

        def _fake_create(*args, **kwargs):
            rt = FakeRunner()
            self.runners.append(rt)
            return rt

        with monkey.patch_scope([(convirt.api, 'create', _fake_create)]):
            self.dom = convirt.domain.Domain(minimal_dom_xml(),
                                             convirt.config.current())


class FakeRunner(object):
    def __init__(self):
        self.stopped = False
        self.started = False
        self.setup_done = False
        self.teardown_done = False
        self.configured = False
        self.uuid = '00000000-0000-0000-0000-000000000000'

    def setup(self, *args, **kwargs):
        self.setup_done = True

    def teardown(self, *args, **kwargs):
        self.teardown_done = True

    def start(self, *args, **kwargs):
        self.started = True

    def stop(self):
        self.stopped = True

    def configure(self, *args, **kwargs):
        self.configured = True


def minimal_dom_xml(vm_uuid=None):
    vm_uuid = str(uuid.uuid4()) if vm_uuid is None else vm_uuid
    return """<?xml version="1.0" encoding="utf-8"?>
<domain type="kvm" xmlns:ovirt="http://ovirt.org/vm/tune/1.0">
  <name>testVm</name>
  <uuid>{vm_uuid}</uuid>
  <maxMemory>16384</maxMemory>
  <devices>
    <emulator>rkt</emulator>
    <disk type='file' device='disk' snapshot='no'>
      <driver name='qemu' type='raw' cache='none' error_policy='stop' io='threads'/>
      <source file='/rhev/data-center/00000001-0001-0001-0001-00000000027f/43db3789-bb16-40bd-a9fc-3cced1b23ea6/images/90bece76-2df6-4a88-bfc8-f6f7461b7b8b/844e5378-6700-45ba-a846-67eba730e24b'>
        <seclabel model='selinux' labelskip='yes'/>
      </source>
      <backingStore/>
      <target dev='vda' bus='virtio'/>
      <serial>90bece76-2df6-4a88-bfc8-f6f7461b7b8b</serial>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
    </disk>
  </devices>
</domain>
""".format(vm_uuid=vm_uuid)
