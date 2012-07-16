#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common utilities tests. Requirements:

 * Internet access with working DNS

 * tests ran by root or bin/python setuid or bin/python setcap CAP_NET_RAW
   (this is required because there's a pure Python ping implementation used)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import textwrap
import sys

from django.test import TestCase
from unittest import skipIf

from ralph.discovery.models import Device, DeviceType
from ralph.discovery.models import DeviceModelGroup
from ralph.discovery.models import MarginKind, DeprecationKind
from ralph.util import pricing


EXISTING_DOMAIN = 'www.allegro.pl'
NON_EXISTENT_DOMAIN = 'nxdomain.allegro.pl'
NON_EXISTENT_HOST_IP = '11.255.255.254'

IP2HOST_IP = '8.8.8.8'
IP2HOST_HOSTNAME_REGEX = r'.*google.*'


class NetworkTest(TestCase):

    @skipIf(sys.platform in ('darwin',), "Ping on MacOS X requires root.")
    def test_ping(self):
        from ralph.util.network import ping
        # existing domain; big timeout for running tests through GPRS
        msg = textwrap.dedent("""
            {} is not pingable from Python. Things you might want to check:
            * are you connected to the Internet
            * is this domain pingable from your terminal
            * is your python binary capped with setcap CAP_NET_RAW
              or
            * are you running tests from root
              or
            * are you using setuid bin/python""".format(
                EXISTING_DOMAIN)).strip()
        self.assertIsNotNone(ping(EXISTING_DOMAIN, 2), msg)
        self.assertTrue(ping(EXISTING_DOMAIN, 2) > 0)
        # non-existent domain
        self.assertIsNone(ping(NON_EXISTENT_DOMAIN))
        # non-pingable host
        self.assertIsNone(ping(NON_EXISTENT_HOST_IP))

    def test_hostname(self):
        from ralph.util.network import hostname
        # existing host
        self.assertIsNotNone(hostname(IP2HOST_IP))
        self.assertIsNotNone(re.match(IP2HOST_HOSTNAME_REGEX,
            hostname(IP2HOST_IP)))
        # non-existent host
        self.assertIsNone(hostname(NON_EXISTENT_HOST_IP))

class PricingTest(TestCase):
    def test_rack_server(self):
        dev = Device.create(sn='xxx', model_type=DeviceType.rack_server,
                            model_name='xxx')
        dmg = DeviceModelGroup(name='XXX')
        dmg.price = 1337
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        pricing.device_update_cached(dev)

        self.assertEquals(dev.cached_price, 1337)

    def test_manual_price(self):
        dev = Device.create(sn='xxx', model_type=DeviceType.rack_server,
                            model_name='xxx')
        dmg = DeviceModelGroup(name='XXX')
        dmg.price = 1337
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        dev.price = 238
        dev.save()
        pricing.device_update_cached(dev)

        self.assertEquals(dev.cached_price, 238)

    def test_blade_server(self):
        encl = Device.create(sn='xxxx', model_type=DeviceType.blade_system,
                            model_name='xxx encl')
        dev = Device.create(sn='xxx', model_type=DeviceType.blade_server,
                            model_name='xxx', parent=encl)

        encl_dmg = DeviceModelGroup(name='XXX encl')
        encl_dmg.slots = 4
        encl_dmg.price = 65535
        encl_dmg.save()
        encl.model.group = encl_dmg
        encl.model.save()

        dmg = DeviceModelGroup(name='XXX')
        dmg.price = 1337
        dmg.slots = 1
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        pricing.device_update_cached(encl)
        pricing.device_update_cached(dev)

        self.assertEquals(dev.cached_price, 17720.75)
        self.assertEquals(encl.cached_price, 49151.25)
        self.assertEquals(dev.cached_price + encl.cached_price, 65535 + 1337)

    def test_cost(self):
        dev = Device.create(sn='xxx', model_type=DeviceType.rack_server,
                            model_name='xxx')
        dmg = DeviceModelGroup(name='XXX')
        dmg.price = 100
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        dev.margin_kind = MarginKind(name='50%', margin=50)
        dev.margin_kind.save()
        dev.deprecation_kind = DeprecationKind(name='10 months', months=10)
        dev.deprecation_kind.save()
        dev.save()
        pricing.device_update_cached(dev)

        self.assertEqual(dev.cached_cost, 15)
