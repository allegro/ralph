# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.test import TestCase

from ralph.cmdb.models_ci import (
    CI, CIType, CIRelation, CI_RELATION_TYPES, CI_TYPES
)
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import Device, DeviceType, DeprecationKind
from ralph.ui.tests.global_utils import login_as_su

CURRENT_DIR = settings.CURRENT_DIR


class TestReportsServices(TestCase):
    fixtures = [
        '0_types.yaml',
        '1_attributes.yaml',
        '2_layers.yaml',
        '3_prefixes.yaml'
    ]

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

    def test_user_login(self):
        self.assertTrue(self.client)

    def test_reports_devices(self):
        self.assertEqual(self.service.name, 'allegro.pl')
        self.assertEqual(self.db_service.name, self.service.name)

    def test_reports_venture(self):
        self.assertEqual(self.venture.name, 'allegro_prod')
        self.assertEqual(self.ci_venture.name, self.venture.name)

    def test_reports_relation(self):
        self.assertEqual(self.relation.child.type_id, CI_TYPES.SERVICE)
        self.assertEqual(self.relation.parent.type_id, CI_TYPES.VENTURE)
        self.assertNotEqual(self.relation.child.type_id, CI_TYPES.VENTURE)

    def test_reports_client(self):
        url = '/ui/reports/services/'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        invalid_relation = report.context['invalid_relation']
        serv_without_ven = report.context['serv_without_ven']
        self.assertEqual(invalid_relation[0].name, 'allegro.pl')
        self.assertEqual(len(invalid_relation), 1)
        self.assertEqual(len(serv_without_ven), 0)
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
        re_serv_without_ven = reload_report.context['serv_without_ven']
        self.assertEqual(len(re_invalid_relation), 1)
        self.assertEqual(len(re_serv_without_ven), 1)


class TestReportsDevices(TestCase):
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
        url ='/ui/reports/devices/?no_support=on'
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
        url ='/ui/reports/devices/?no_purchase=on'
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
        url ='/ui/reports/devices/?no_venture=on'
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
        url ='/ui/reports/devices/?no_role=on'
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
        url ='/ui/reports/devices/?s_start=2003-01-01&s_end=2003-01-03'
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
        url ='/ui/reports/devices/?d_start=2001-12-30&d_end=2002-01-02'
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
        url ='/ui/reports/devices/?w_start=2005-01-01&w_end=2005-01-03'
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

class TestReportsVentures(TestCase):
    """
    I need test!
    """
    pass


class TestReportsMargins(TestCase):
    """
    I need test!
    """
    pass
