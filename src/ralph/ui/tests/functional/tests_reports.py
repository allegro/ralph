# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.test import TestCase
from unittest import skip

from ralph.cmdb.models_ci import (
    CI,
    CIType,
    CIRelation,
    CI_RELATION_TYPES,
    CI_TYPES,
)
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import (
    Device,
    DeviceType,
    DeprecationKind,
    MarginKind,
)
from ralph.ui.tests.global_utils import login_as_su
from ralph.ui.tests.util import create_device
from ralph.util.pricing import get_device_price

CURRENT_DIR = settings.CURRENT_DIR


class AccessToReportsTest(TestCase):

    def setUp(self):
        self.client = login_as_su(
            username='ralph_root',
            password='top_securet',
            email='ralph1@ralph.local',
            is_staff=False,
            is_superuser=False,
        )
        self.client_su = login_as_su()

        self.report_urls = [
            '/ui/reports/margins/',
            '/ui/reports/devices/',
            '/ui/reports/services/',
            '/ui/reports/ventures/',
            '/ui/reports/device_prices_per_venture/',
        ]

    @skip("Not testable async report.")
    def test_no_perms_to_reports(self):
        for url in self.report_urls:
            get_request = self.client.get(url)
            self.assertEqual(get_request.status_code, 403)

    @skip("Not testable async report.")
    def test_perms_to_reports(self):
        for url in self.report_urls:
            get_request = self.client_su.get(url)
            self.assertEqual(get_request.status_code, 200)


class ReportsServicesTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.service = CI(
            name='allegro.pl',
            type=CIType.objects.get(id=CI_TYPES.SERVICE)
        )
        self.service.save()
        self.db_service = CI.objects.get(id=self.service.id)
        self.venture = CI(
            name='allegro_prod',
            type=CIType.objects.get(id=CI_TYPES.VENTURE)
        )
        self.venture.save()
        self.ci_venture = CI.objects.get(id=self.venture.id)
        self.relation = CIRelation(
            parent=self.ci_venture,
            child=self.db_service,
            type=CI_RELATION_TYPES.CONTAINS,
        )
        self.relation.save()

    @skip("Not testable async report.")
    def test_user_login(self):
        self.assertTrue(self.client)

    @skip("Not testable async report.")
    def test_reports_devices(self):
        self.assertEqual(self.service.name, 'allegro.pl')
        self.assertEqual(self.db_service.name, self.service.name)

    @skip("Not testable async report.")
    def test_reports_venture(self):
        self.assertEqual(self.venture.name, 'allegro_prod')
        self.assertEqual(self.ci_venture.name, self.venture.name)

    @skip("Not testable async report.")
    def test_reports_relation(self):
        self.assertEqual(self.relation.child.type_id, CI_TYPES.SERVICE)
        self.assertEqual(self.relation.parent.type_id, CI_TYPES.VENTURE)
        self.assertNotEqual(self.relation.child.type_id, CI_TYPES.VENTURE)

    @skip("Not testable async report.")
    def test_reports_views(self):
        url = '/ui/reports/services/'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        invalid_relation = report.context['invalid_relation']
        services_without_venture = report.context['services_without_venture']
        self.assertEqual(invalid_relation[0].name, 'allegro.pl')
        self.assertEqual(len(invalid_relation), 1)
        self.assertEqual(len(services_without_venture), 0)
        # local service for tests
        service = CI(name='ceneo.pl', type=CIType.objects.get(
            id=CI_TYPES.SERVICE)
        )
        service.save()
        # local venture for tests
        venture = CI(name='allegro_prod', type=CIType.objects.get(
            id=CI_TYPES.VENTURE)
        )
        venture.save()
        reload_report = self.client.get(url, follow=True)
        re_invalid_relation = reload_report.context['invalid_relation']
        re_services_without_venture = reload_report.context[
            'services_without_venture']
        self.assertEqual(len(re_invalid_relation), 1)
        self.assertEqual(len(re_services_without_venture), 0)


class ReportsDevicesTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        venture = Venture(name='venture', symbol='ventureSymbol')
        venture.save()
        self.venture = venture
        venture_role = VentureRole(name='role', venture=self.venture)
        venture_role.save()
        self.venture_role = venture_role
        d_kind = DeprecationKind(name='12 months', months=12)
        d_kind.save()
        self.kind = DeprecationKind.objects.get(name='12 months')
        # Cross - devices
        self.device_after_deprecation = Device.create(
            sn='device_after_deprecation',
            deprecation_kind=self.kind,
            support_expiration_date=datetime.datetime(2003, 01, 02),
            purchase_date=datetime.datetime(2001, 01, 01),
            warranty_expiration_date=datetime.datetime(2005, 01, 02),
            venture=self.venture,
            venture_role=self.venture_role,
            model_name='xxx',
            model_type=DeviceType.unknown,
        )
        self.device_after_deprecation.name = 'Device1'
        self.device_after_deprecation.save()
        self.device_with_blanks = Device.create(
            sn='device_with_blanks',
            deprecation_date=None,
            deprecation_kind=None,
            support_expiration_date=None,
            purchase_date=None,
            venture=None,
            venture_role=None,
            model_name='xxx',
            model_type=DeviceType.unknown,
        )
        self.device_with_blanks.name = 'Device2'
        self.device_with_blanks.save()
        # Range - Devices

    def test_models(self):
        db = Device.objects.get(sn='device_after_deprecation')
        self.assertEqual(unicode(db.deprecation_date), '2002-01-01 00:00:00')
        self.assertNotEqual(db.deprecation_date, None)
        self.assertNotEqual(db.deprecation_kind, None)
        self.assertNotEqual(db.purchase_date, None)
        self.assertNotEqual(db.venture, None)
        self.assertNotEqual(db.venture_role, None)
        db = Device.objects.get(sn='device_with_blanks')
        self.assertEqual(db.deprecation_date, None)
        self.assertEqual(db.deprecation_kind, None)
        self.assertEqual(db.purchase_date, None)
        self.assertEqual(db.venture, None)
        self.assertEqual(db.venture_role, None)

    def test_after_deprecation(self):
        url = '/ui/reports/devices/?deprecation=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_name = self.device_after_deprecation.name
        dev_id = self.device_after_deprecation.id
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], datetime.datetime(2002, 01, 01))
        self.assertEqual(len(form), 1)

    def test_no_deprecation_date(self):
        url = '/ui/reports/devices/?no_deprecation=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)
        self.assertEqual(len(form), 1)

    def test_no_deprecation_kind(self):
        url = '/ui/reports/devices/?no_margin=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)

    def test_no_support_date(self):
        url = '/ui/reports/devices/?no_support=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)
        self.assertEqual(len(form), 1)
        self.assertNotEqual(form[0][1], '2000-01-02 00:00:00')

    def test_no_purchase_date(self):
        url = '/ui/reports/devices/?no_purchase=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)
        self.assertEqual(len(form), 1)
        self.assertNotEqual(form[0][1], '2000-01-03 00:00:00')

    def test_no_venture(self):
        url = '/ui/reports/devices/?no_venture=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)
        self.assertEqual(len(form), 1)
        self.assertNotEqual(form[0][1], self.venture)

    def test_no_role(self):
        url = '/ui/reports/devices/?no_role=on'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_with_blanks.id
        dev_name = self.device_with_blanks.name
        self.assertEqual(len(form), 1)
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], None)
        self.assertNotEqual(form[0][1], self.venture_role)

    def test_range_support(self):
        url = '/ui/reports/devices/?s_start=2003-01-01&s_end=2003-01-03'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_after_deprecation.id
        dev_name = self.device_after_deprecation.name
        self.assertEqual(len(form), 1)
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], datetime.datetime(2003, 01, 02))

    def test_range_deprecation(self):
        url = '/ui/reports/devices/?d_start=2001-12-30&d_end=2002-01-02'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_after_deprecation.id
        dev_name = self.device_after_deprecation.name
        self.assertEqual(len(form), 1)
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], datetime.datetime(2002, 01, 01))

    def test_range_warranty(self):
        url = '/ui/reports/devices/?w_start=2005-01-01&w_end=2005-01-03'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        form = report.context['rows']
        dev_id = self.device_after_deprecation.id
        dev_name = self.device_after_deprecation.name
        self.assertEqual(len(form), 1)
        name = u'<a href="/ui/search/info/%s">%s</a> (%s)' % (
            dev_id, dev_name, dev_id
        )
        self.assertEqual(form[0][0], name)
        self.assertEqual(form[0][1], datetime.datetime(2005, 01, 02))


class ReportsPriceDeviceVentureTest(TestCase):

    def setUp(self):
        self.client = login_as_su()

        venture = Venture(name='Infra').save()
        self.venture = Venture.objects.get(name='Infra')

        venture = Venture(name='Blade').save()
        self.venture_blade = Venture.objects.get(name='Blade')

        DeprecationKind(name='Default', months=24).save()
        self.deprecation_kind = DeprecationKind.objects.get(name='Default')

        srv1 = {
            'sn': 'srv-1',
            'model_name': 'server',
            'model_type': DeviceType.virtual_server,
            'venture': self.venture,
            'name': 'Srv 1',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        srv1_cpu = {
            'model_name': 'Intel PCU1',
            'label': 'CPU 1',
            'priority': 0,
            'family': 'Intsels',
            'price': 120,
            'count': 2,
            'speed': 1200
        }
        srv1_memory = {
            'priority': 0,
            'family': 'Noname RAM',
            'label': 'Memory 1GB',
            'price': 100,
            'speed': 1033,
            'size': 512,
            'count': 6,
        }
        srv1_storage = {
            'model_name': 'Store 1TB',
            'label': 'store 1TB',
            'priority': 0,
            'family': 'Noname Store',
            'price': 180,
            'count': 10,
        }
        create_device(
            device=srv1,
            cpu=srv1_cpu,
            memory=srv1_memory,
            storage=srv1_storage
        )
        self.srv1 = Device.objects.get(sn='srv-1')

        srv2 = {
            'sn': 'srv-2',
            'model_name': 'server',
            'model_type': DeviceType.virtual_server,
            'venture': self.venture,
            'name': 'Srv 1',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        create_device(device=srv2)
        self.srv2 = Device.objects.get(sn='srv-2')

        rack = {
            'sn': 'rack-1',
            'model_name': 'rack1',
            'model_type': DeviceType.rack,
            'price': 5000,
            'name': 'rack1',
            'model_group': 'Rack Group',
            'model_group_slots': 20,
        }
        create_device(device=rack)
        self.rack = Device.objects.get(sn='rack-1')

        blc = {
            'sn': 'blc-1',
            'model_name': 'blade-center',
            'model_type': DeviceType.blade_system,
            'venture': self.venture_blade,
            'name': 'Blc 1',
            'parent': self.rack,
            'price': 10000,
            'model_group': 'BladeCenters Group',
            'model_group_slots': 10,
        }
        create_device(device=blc)
        self.blc = Device.objects.get(sn='blc-1')

        bls1 = {
            'sn': 'bls-1',
            'model_name': 'blade-server',
            'model_type': DeviceType.blade_server,
            'venture': self.venture_blade,
            'parent': self.blc,
            'name': 'Bls 1',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        bls1_cpu = {
            'model_name': 'Intel PCU2',
            'label': 'CPU 2',
            'priority': 0,
            'family': 'Intsels',
            'price': 140,
            'count': 4,
            'speed': 2000,
        }
        create_device(device=bls1, cpu=bls1_cpu)
        self.bls1 = Device.objects.get(sn='bls-1')
        bls2 = {
            'sn': 'bls-2',
            'model_name': 'blade-server',
            'model_type': DeviceType.blade_server,
            'venture': self.venture_blade,
            'parent': self.blc,
            'name': 'Bls 2',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        bls2_memory = {
            'priority': 0,
            'family': 'Noname RAM2',
            'label': 'Ram 2048',
            'price': 80,
            'speed': 1033,
            'size': 2048,
            'count': 10,
        }
        bls2_cpu = {
            'model_name': 'Intel PCU3',
            'label': 'CPU 3',
            'priority': 0,
            'family': 'Intsels',
            'price': 120,
            'count': 2,
            'speed': 1500,
        }

        create_device(device=bls2, cpu=bls2_cpu, memory=bls2_memory)
        self.bls2 = Device.objects.get(sn='bls-2')

        bls3 = {
            'sn': 'bls-3',
            'model_name': 'blade-server',
            'model_type': DeviceType.blade_server,
            'venture': self.venture_blade,
            'parent': self.blc,
            'name': 'Bls 3',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        bls3_memory = {
            'priority': 0,
            'family': 'Noname RAM3',
            'label': 'Ram 512',
            'price': 80,
            'speed': 1033,
            'size': 512,
            'count': 2,
        }
        create_device(device=bls3, memory=bls3_memory)
        self.bls3 = Device.objects.get(sn='bls-3')

        bls4 = {
            'sn': 'bls-4',
            'model_name': 'blade-server',
            'model_type': DeviceType.blade_server,
            'venture': self.venture_blade,
            'parent': self.blc,
            'name': 'Bls 4',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
            'price': 3000,
        }
        create_device(device=bls4)
        self.bls4 = Device.objects.get(sn='bls-4')

    def test_create_device(self):
        ''' Tests util create_device '''

        devices = Device.objects.filter(name='Srv 1')
        self.assertIsNotNone(devices)

    @skip("Not testable async report.")
    def test_view_devices_with_components_in_venture(self):
        ''' Tests device with local components, with praces from catalog '''
        venture = Venture.objects.get(name='Infra')
        url = '/ui/reports/device_prices_per_venture/?venture=%s' % venture.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices_list = response.context_data.get('rows')
        devices = devices_list.pop()
        for dev in devices.get('components', []):
            total = 0
            for component in dev.get('components', []):
                total += component.get('price')
            self.assertEqual(dev.get('price'), total)

    @skip("Not testable async report.")
    def test_deprecated_device_with_components_in_venture(self):
        before_deprecated = get_device_price(self.srv1)
        self.assertEqual(before_deprecated, 2640)

        self.srv1.purchase_date = datetime.datetime(1999, 1, 1, 0, 0)
        self.srv1.save()
        dev = Device.objects.get(sn='srv-1')

        self.assertEqual(
            dev.deprecation_date, datetime.datetime(2001, 1, 1, 0, 0)
        )

        after_deprecated = get_device_price(dev)
        self.assertEqual(after_deprecated, 0)

        venture = Venture.objects.get(name='Infra')
        url = '/ui/reports/device_prices_per_venture/?venture=%s' % venture.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')

        devices_list = response.context_data.get('rows')
        devices = devices_list.pop()
        for dev in devices.get('components', []):
            total = 0
            for component in dev.get('components', []):
                total += component.get('price')
            self.assertEqual(dev.get('price'), total)

    @skip("Not testable async report.")
    def test_deleted_device_in_venture(self):
        ''' Tests if deteleted device is see in venture '''

        venture = Venture.objects.get(name='Infra')
        url = '/ui/reports/device_prices_per_venture/?venture=%s' % venture.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')

        self.assertEqual(len(devices), 2)

        self.srv1.deleted = True
        self.srv1.save()

        venture = Venture.objects.get(name='Infra')
        url = '/ui/reports/device_prices_per_venture/?venture=%s' % venture.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')

        self.assertEqual(len(devices), 1)

    @skip("Not testable async report.")
    def test_blade_system(self):
        ''' Test blade system infrastuctire '''

        self.assertIsNotNone(self.blc)
        self.assertIsNotNone(self.bls1)
        self.assertEqual(self.bls1.parent, self.blc)
        self.assertEqual(self.bls2.parent, self.blc)
        self.assertEqual(self.bls3.parent, self.blc)
        self.assertEqual(self.bls4.parent, self.blc)
        self.assertEqual(len(self.blc.child_set.all()), 4)

        venture = Venture.objects.get(name='Blade')
        url = ('/ui/reports/device_prices_per_venture/?venture=%s'
               % self.venture_blade.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')

        self.assertEqual(len(devices), 5)

    @skip("Not testable async report.")
    def test_blade_system_with_deprecated_device(self):
        self.bls2.purchase_date = datetime.datetime(1999, 1, 1, 0, 0)
        self.bls2.save()

        venture = Venture.objects.get(name='Blade')
        url = ('/ui/reports/device_prices_per_venture/?venture=%s'
               % self.venture_blade.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')

        self.assertEqual(len(devices), 5)

    @skip("Not testable async report.")
    def test_blade_system_with_deleted_device(self):
        self.bls3.deleted = True
        self.bls3.save()
        dev = Device.objects.get(sn='srv-1')

        venture = Venture.objects.get(name='Blade')
        url = ('/ui/reports/device_prices_per_venture/?venture=%s'
               % self.venture_blade.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        devices = response.context_data.get('rows')
        self.assertEqual(len(devices), 4)


class ReportsVenturesTest(TestCase):

    """
    I need test!
    """
    pass


class ReportsMarginsTest(TestCase):

    """
    I need test!
    """
    pass
