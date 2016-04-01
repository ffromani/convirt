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
from __future__ import absolute_import

import libvirt

import convirt
import convirt.config.environ
import convirt.connection
import convirt.events

from . import testlib
from six.moves import range


NUM = 5  # random "low" number


class ConnectionTests(testlib.TestCase):

    def setUp(self):
        convirt.events.root.clear()

    def test_without_registered(self):
        self.assertEquals(tuple(sorted(convirt.events.root.registered)),
                          tuple())

    def test_register_any(self):
        events = (
            libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
            libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
            libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE,
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON,
            libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS,
            libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_JOB,
            libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG,
        )

        conn = convirt.connection.Connection()
        for ev in events:
            conn.domainEventRegisterAny(None, ev, _handler, ev)

        self.assertEquals(tuple(sorted(events)),
                          tuple(sorted(convirt.events.root.registered)))

    def test_register_specific_dom(self):
        evt = libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE

        called = [False]

        def _cb(*args, **kwargs):
            called[0] = True

        conn = convirt.connection.Connection()
        dom = convirt.domain.Domain(testlib.minimal_dom_xml(),
                                    convirt.config.environ.current())
        conn.domainEventRegisterAny(dom, evt, _cb, None)

        # FIXME
        self.assertEquals(tuple(),
                          tuple(sorted(convirt.events.root.registered)))
        self.assertEquals((evt,),
                          tuple(sorted(dom.events.registered)))

        dom.events.fire(evt, None)
        self.assertTrue(called[0])

    def test_register_multiple_callbacks(self):
        evt = libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE

        called = [False] * NUM

        def _cb(conn, dom, opaque):
            called[opaque] = True

        conn = convirt.connection.Connection()
        for idx in range(NUM):
            conn.domainEventRegisterAny(None, evt, _cb, None)

        self.assertFalse(all(called))
        for idx in range(NUM):
            convirt.events.fire(evt, None, idx)
        self.assertTrue(all(called))

    def test_fire_unknown_event(self):
        self.assertNotRaises(convirt.events.fire,
                             libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                             None)

    def test_fire_unknown_event_through_dom(self):
        dom = convirt.domain.Domain(testlib.minimal_dom_xml(),
                                    convirt.config.environ.current())
        self.assertNotRaises(dom.events.fire,
                             libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                             None)


def _handler(*args, **kwargs):
    pass
