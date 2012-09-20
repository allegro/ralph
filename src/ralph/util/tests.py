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

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from unittest import skipIf
from tastypie.models import ApiKey

from ralph.business.models import Venture
from ralph.discovery.models import Device, DeviceType
from ralph.discovery.models import DeviceModelGroup
from ralph.discovery.models import MarginKind, DeprecationKind
from ralph.util import pricing


EXISTING_DOMAIN = settings.SANITY_CHECK_PING_ADDRESS
NON_EXISTENT_DOMAIN = 'nxdomain.allegro.pl'
NON_EXISTENT_HOST_IP = '11.255.255.254'

IP2HOST_IP = settings.SANITY_CHECK_IP2HOST_IP
IP2HOST_HOSTNAME_REGEX = settings.SANITY_CHECK_IP2HOST_HOSTNAME_REGEX


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
        dev = Device.create(sn='device', model_type=DeviceType.rack_server,
                            model_name='device')
        dmg = DeviceModelGroup(name='DeviceModelGroup')
        dmg.price = 1337
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        pricing.device_update_cached(dev)

        self.assertEquals(dev.cached_price, 1337)

    def test_manual_price(self):
        dev = Device.create(sn='device', model_type=DeviceType.rack_server,
                            model_name='device')
        dmg = DeviceModelGroup(name='DeviceModelGroup')
        dmg.price = 1337
        dmg.save()
        dev.model.group = dmg
        dev.model.save()

        dev.price = 238
        dev.save()
        pricing.device_update_cached(dev)

        self.assertEquals(dev.cached_price, 238)

    def test_blade_server(self):
        encl = Device.create(sn='devicex', model_type=DeviceType.blade_system,
                            model_name='device encl')
        dev = Device.create(sn='device', model_type=DeviceType.blade_server,
                            model_name='device', parent=encl)

        encl_dmg = DeviceModelGroup(name='DeviceModelGroup encl')
        encl_dmg.slots = 4
        encl_dmg.price = 65535
        encl_dmg.save()
        encl.model.group = encl_dmg
        encl.model.save()

        dmg = DeviceModelGroup(name='DeviceModelGroup')
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
        dev = Device.create(sn='device', model_type=DeviceType.rack_server,
                            model_name='device')
        dmg = DeviceModelGroup(name='DeviceModelGroup')
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

class ApiTest(TestCase):
    def _save_ventures(self, count):
        id_list = []
        for i in range(0, count):
            v = Venture(name=i, symbol=i)
            v.save()
            id_list.append(v.id)
        return id_list

    def test_throttling(self):
        user = User.objects.create_user('api_user', 'test@mail.local', 'password')
        user.save()
        api_key = ApiKey.objects.get(user=user)
        data = {'format': 'json', 'username': user.username, 'api_key': api_key.key}
        status_list = []
        id_list = self._save_ventures(5)

        for i, id in enumerate(id_list):
            path = "/api/v0.9/venture/%s" % i
            response = self.client.get(path=path, data=data, follow=True)
            status_list.append(response.status_code)

        self.assertListEqual([200, 200, 403, 403, 403], status_list)