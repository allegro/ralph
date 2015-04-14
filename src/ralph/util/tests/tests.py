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

import ipaddr
import re
import textwrap
from datetime import date, datetime, timedelta
from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from tastypie.models import ApiKey
from unittest import skip

from ralph.business.models import Venture
from ralph.cmdb import models_ci
from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    DeprecationKind,
    Device,
    DeviceType,
    DiskShare,
    DiskShareMount,
    IPAddress,
    MarginKind,
)
from ralph.discovery.tests import util as discovery_util
from ralph.util import api_pricing, api_scrooge
from ralph.util.tests import utils
from ralph.util import api

EXISTING_DOMAIN = 'www.google.com'
NON_EXISTENT_DOMAIN = 'nxdomain.allegro.pl'
NON_EXISTENT_HOST_IP = '11.255.255.254'

IP2HOST_IP = settings.SANITY_CHECK_IP2HOST_IP
IP2HOST_HOSTNAME_REGEX = settings.SANITY_CHECK_IP2HOST_HOSTNAME_REGEX

THROTTLE_AT = settings.API_THROTTLING['throttle_at']


class NetworkTest(TestCase):

    @skip('uses external resources')
    # @skipIf(sys.platform in ('darwin',), "Ping on MacOS X requires root.")
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

    @skip('uses external resources')
    def test_hostname(self):
        from ralph.util.network import hostname
        # existing host
        self.assertIsNotNone(hostname(IP2HOST_IP))
        self.assertIsNotNone(re.match(IP2HOST_HOSTNAME_REGEX,
                                      hostname(IP2HOST_IP)))
        # non-existent host
        self.assertIsNone(hostname(NON_EXISTENT_HOST_IP))


class ApiTest(TestCase):

    def setUp(self):
        cache.delete("api_user_accesses")

    def _save_ventures(self, count):
        id_list = []
        for i in range(0, count):
            v = Venture(name=i, symbol=i)
            v.save()
            id_list.append(v.id)
        return id_list

    def test_throttling(self):
        user = User.objects.create_user(
            'api_user',
            'test@mail.local',
            'password'
        )
        user.save()
        api_key = ApiKey.objects.get(user=user)
        data = {
            'format': 'json',
            'username': user.username,
            'api_key': api_key.key
        }
        status_list = []
        id_list = self._save_ventures(THROTTLE_AT + 2)

        for id in id_list:
            path = "/api/v0.9/venture/%s" % id
            response = self.client.get(path=path, data=data, follow=True)
            status_list.append(response.status_code)
        gen_list = [200 for x in range(0, THROTTLE_AT)]
        gen_list.append(429)
        gen_list.append(429)
        self.maxDiff = None
        self.assertListEqual(gen_list, status_list)

    def test_get_api_key_when_there_is_no_API_key(self):
        self.assertRaises(
            api.NoApiKeyError,
            api._get_api_key,
            utils.AttributeDict({
                'REQUEST': {},
                'META': {}
            })
        )

    def test_get_api_key_from_REQUEST(self):
        test_api_key = 'test_api_key'
        results = api._get_api_key(
            utils.AttributeDict({
                'REQUEST': {'api_key': test_api_key},
                'META': {}
            })
        )
        self.assertEquals(test_api_key, results)

    def test_get_api_key_from_META(self):
        test_api_key = 'Token test_api_key'
        results = api._get_api_key(
            utils.AttributeDict({
                'REQUEST': {},
                'META': {'HTTP_AUTHORIZATION': test_api_key}
            })
        )
        self.assertEquals(test_api_key.split(' ')[-1], results)

    def test_get_user_by_name(self):
        user = User.objects.create_superuser('test', 'test@test.test', 'test')
        results = api.get_user(
            utils.AttributeDict({
                'REQUEST': {'username': user.username},
                'META': {}
            })
        )
        self.assertEquals(user, results)

    @patch.object(api, '_get_api_key', lambda x: 'test')
    def test_get_user_by_api_key(self):
        user = User.objects.create_superuser('test', 'test@test.test', 'test')
        user.api_key.key = 'test'
        user.api_key.save()
        results = api.get_user(
            utils.AttributeDict({
                'REQUEST': {},
                'META': {}
            })
        )
        self.assertEquals(user, results)

    @patch.object(api, '_get_api_key', lambda x: 'test')
    def test_get_user_when_user_does_not_exist(self):
        user = User.objects.create_superuser('test', 'test@test.test', 'test')
        self.assertRaises(
            User.DoesNotExist,
            api.get_user,
            utils.AttributeDict({
                'REQUEST': {},
                'META': {}
            }),
        )

    def test_get_user_when_there_is_wrong_api_key(self):
        user = User.objects.create_superuser('test', 'test@test.test', 'test')
        self.assertRaises(
            api.NoApiKeyError,
            api.get_user,
            utils.AttributeDict({
                'REQUEST': {},
                'META': {}
            }),
        )


class ApiPricingTest(TestCase):

    def setUp(self):
        self.venture, created = Venture.objects.get_or_create(
            name="Sample venture",
        )
        self.venture.save()

        self.device, created = Device.objects.get_or_create(
            name="Device1",
            venture=self.venture,
        )
        self.device_without_venture, created = Device.objects.get_or_create(
            name="Device2",
        )

        self.ip1 = IPAddress(address='1.1.1.1', device=self.device)
        self.ip2 = IPAddress(address='2.2.2.2', venture=self.venture)
        self.ip1.save()
        self.ip2.save()

        self.device.save()
        self.device_without_venture.save()

    def test_get_device_by_name_with_venture(self):
        # device with venture
        device1 = api_pricing.get_device_by_name("Device1")
        self.assertEqual(device1['device_id'], self.device.id)
        self.assertEqual(device1['venture_id'], self.venture.id)

    def test_get_device_by_name_without_venture(self):
        # device without venture
        device2 = api_pricing.get_device_by_name("Device2")
        self.assertEqual(device2['device_id'], self.device_without_venture.id)
        self.assertIsNone(device2['venture_id'])

    def test_get_device_by_name_wrong_name(self):
        # device does not exist
        device3 = api_pricing.get_device_by_name("Device3")
        self.assertEqual(device3, {})

    def test_get_ip_info(self):
        result = api_pricing.get_ip_info(ipaddress='1.1.1.1')
        self.assertEquals(result, {
            'device_id': self.device.id,
            'venture_id': self.venture.id,
        })

    def test_get_ip_info_without_device(self):
        result = api_pricing.get_ip_info(ipaddress='2.2.2.2')
        self.assertEquals(result, {
            'venture_id': self.venture.id,
        })

    def test_get_ip_info_empty(self):
        result = api_pricing.get_ip_info(ipaddress='3.3.3.3')
        self.assertEquals(result, {})


class ApiScroogeTest(TestCase):

    def _init_vips(self):
        self.vips = discovery_util.LoadBalancerVirtualServerFactory.create_batch(2)

    def _vip2api(self, lbvs):
        return {
            'vip_id': lbvs.id,
            'type_id': lbvs.load_balancer_type_id,
            'name': lbvs.name,
            'ip_address': str(lbvs.address.address),
            'port': lbvs.port,
            'type': lbvs.load_balancer_type.name,
            'device_id': lbvs.device_id,
            'service_id': lbvs.service_id,
            'environment_id': lbvs.device_environment_id,
        }

    def test_get_vips(self):
        self._init_vips()
        result = [v for v in api_scrooge.get_vips()]
        vips_dict = map(self._vip2api, self.vips)
        self.assertEqual(result, vips_dict)

    def test_get_vips_parent_service(self):
        self._init_vips()
        result = [v for v in api_scrooge.get_vips(
            parent_service_uid=self.vips[0].device.service.uid
        )]
        vips_dict = map(self._vip2api, self.vips[0:1])
        self.assertEqual(result, vips_dict)

    def test_get_vips_load_balancer_type(self):
        self._init_vips()
        result = [v for v in api_scrooge.get_vips(
            load_balancer_type=self.vips[0].load_balancer_type.name
        )]
        vips_dict = map(self._vip2api, self.vips[0:1])
        self.assertEqual(result, vips_dict)

    def _init_db(self):
        self.databases = discovery_util.DatabaseFactory.create_batch(2)

    def _db2api(self, db):
        return {
            'database_id': db.id,
            'type_id': db.database_type_id,
            'name': db.name,
            'type': db.database_type.name,
            'parent_device_id': db.parent_device_id,
            'service_id': db.service_id,
            'environment_id': db.device_environment_id,
        }

    def test_get_databases(self):
        self._init_db()
        result = [v for v in api_scrooge.get_databases()]
        databases_dict = map(self._db2api, self.databases)
        self.assertEqual(result, databases_dict)

    def test_get_databases_parent_service(self):
        self._init_db()
        result = [v for v in api_scrooge.get_databases(
            parent_service_uid=self.databases[0].parent_device.service.uid
        )]
        databases_dict = map(self._db2api, self.databases[:1])
        self.assertEqual(result, databases_dict)

    def test_get_databases_type(self):
        self._init_db()
        result = [v for v in api_scrooge.get_databases(
            database_type=self.databases[0].database_type.name
        )]
        databases_dict = map(self._db2api, self.databases[:1])
        self.assertEqual(result, databases_dict)

    def test_get_business_lines(self):
        business_lines = utils.BusinessLineFactory.create_batch(7)
        result = [a for a in api_scrooge.get_business_lines()]
        business_lines_dict = [{
            'name': bl.name,
            'ci_uid': bl.uid,
            'ci_id': bl.id,
        } for bl in business_lines]
        self.assertEquals(result, business_lines_dict)

    def test_get_profit_centers(self):
        profit_centers = utils.ProfitCenterFactory.create_batch(7)
        result = [a for a in api_scrooge.get_profit_centers()]
        profit_centers_dict = [{
            'name': pc.name,
            'ci_uid': pc.uid,
            'ci_id': pc.id,
            'description': None,
            'business_line': None,
        } for pc in profit_centers]
        self.assertEquals(result, profit_centers_dict)

    def test_get_owners(self):
        owners = utils.CIOwnerFactory.create_batch(10)
        result = [a for a in api_scrooge.get_owners()]
        owners_dict = [{
            'id': o.id,
            'profile_id': o.profile_id,
        } for o in owners]
        self.assertEquals(result, owners_dict)

    def test_get_services(self):
        service = utils.ServiceFactory()
        profit_center = utils.ProfitCenterFactory()
        utils.ServiceProfitCenterRelationFactory(
            parent=profit_center,
            child=service,
        )
        business_ownership = utils.ServiceOwnershipFactory.create_batch(
            2,
            ci=service,
            type=models_ci.CIOwnershipType.business,
        )
        technical_ownership = utils.ServiceOwnershipFactory.create_batch(
            3,
            ci=service,
            type=models_ci.CIOwnershipType.technical,
        )
        environments = utils.ServiceEnvironmentRelationFactory.create_batch(
            2,
            parent=service,
        )
        result = [a for a in api_scrooge.get_services()]
        service_dict = {
            'name': service.name,
            'ci_id': service.id,
            'ci_uid': service.uid,
            'symbol': None,
            'profit_center': profit_center.id,
            'business_owners': [bo.owner.id for bo in business_ownership],
            'technical_owners': [to.owner.id for to in technical_ownership],
            'environments': [e.child.id for e in environments],
        }
        self.assertEquals(result, [service_dict])

    def test_get_services_without_profit_center(self):
        service = utils.ServiceFactory()
        result = [a for a in api_scrooge.get_services()]
        service_dict = {
            'name': service.name,
            'ci_id': service.id,
            'ci_uid': service.uid,
            'symbol': None,
            'profit_center': None,
            'technical_owners': [],
            'business_owners': [],
            'environments': [],
        }
        self.assertEquals(result, [service_dict])

    def test_get_services_calc_in_scrooge(self):
        service = utils.ServiceFactory()
        utils.ServiceFactory()  # service not calculated in scrooge
        calc_in_scrooge_attr = models_ci.CIAttribute.objects.get(pk=7)
        service.ciattributevalue_set.create(
            attribute=calc_in_scrooge_attr,
            value=True
        )
        result = [a for a in api_scrooge.get_services(True)]
        service_dict = {
            'name': service.name,
            'ci_id': service.id,
            'ci_uid': service.uid,
            'symbol': None,
            'profit_center': None,
            'technical_owners': [],
            'business_owners': [],
            'environments': [],
        }
        self.assertEquals(result, [service_dict])

    def test_getattr_dunder(self):
        """getattr_dunder works recursively"""

        class A():
            pass

        a = A()
        a.b = A()
        a.b.name = 'spam'
        self.assertEqual(api.getattr_dunder(a, 'b__name'), 'spam')


class UncompressBase64DataTest(TestCase):

    def test_base64_encoded_data(self):
        import base64
        from ralph.util import uncompress_base64_data

        raw = "Zażółć gęślą jaźń.".encode('utf8')
        encoded = base64.b64encode(raw)
        self.assertEqual(uncompress_base64_data(encoded), raw)

    def test_zlib_compressed_data(self):
        import zlib
        from ralph.util import uncompress_base64_data

        raw = "Zażółć gęślą jaźń.".encode('utf8')
        compressed = zlib.compress(raw)
        self.assertEqual(uncompress_base64_data(compressed), raw)

    def test_base64_encoded_zlib_compressed_data(self):
        import base64
        import zlib
        from ralph.util import uncompress_base64_data

        raw = "Zażółć gęślą jaźń.".encode('utf8')
        compressed = zlib.compress(raw)
        encoded = base64.b64encode(compressed)
        self.assertEqual(uncompress_base64_data(encoded), raw)

    def test_wrong_way__zlib_compressed_base64_encoded_data(self):
        """Here the input is made by zlib(base64(raw_data)) instead of
        base64(zlib(raw_data)). uncompress_base64_data should return
        the base64 representation."""
        import base64
        import zlib
        from ralph.util import uncompress_base64_data

        raw = "Zażółć gęślą jaźń.".encode('utf8')
        encoded = base64.b64encode(raw)
        compressed = zlib.compress(encoded)
        self.assertEqual(uncompress_base64_data(compressed), encoded)
