# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from ralph.cmdb.models_ci import CI, CIType, CIRelation, CI_RELATION_TYPES
from ralph.ui.tests.helper import login_as_su


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
        self.ci_type_venture = CIType(name='Venture')
        self.ci_type_venture.save()
        self.ci_type_service = CIType(name='Service')
        self.ci_type_service.save()
        self.service = CI(
            name='allegro.pl',
            type=CIType.objects.get(id=7)
        )
        self.service.save()
        self.db_service = CI.objects.get(id=self.service.id)
        self.venture = CI(
            name='allegro_prod',
            type=CIType.objects.get(id=4)
        )
        self.venture.save()
        self.ci_venture = CI.objects.get(id=self.venture.id)
        self.relation = CIRelation(
            parent=self.ci_venture,
            child=self.db_service,
            type=CI_RELATION_TYPES.CONTAINS,
        )
        self.relation.save()
        self.db_relation = CI.objects.get(pk='1')

    def test_user_login(self):
        self.assertTrue(self.client)

    def test_reports_devices(self):
        self.assertEqual(self.service.name, 'allegro.pl')
        self.assertEqual(self.db_service.name, self.service.name)

    def test_reports_venture(self):
        self.assertEqual(self.venture.name, 'allegro_prod')
        self.assertEqual(self.ci_venture.name, self.venture.name)

    def test_reports_relation(self):
        self.assertEqual(self.relation.child.type_id, 7)
        self.assertEqual(self.relation.parent.type_id, 4)
        self.assertNotEqual(self.relation.child.type_id, 4)

    def test_reports_client(self):
        url = '/ui/reports/services/'
        report = self.client.get(url, follow=True)
        self.assertEqual(report.status_code, 200)
        serv_with_ven = report.context['serv_with_ven']
        serv_without_ven = report.context['serv_without_ven']
        self.assertEqual(serv_with_ven[0].name, 'allegro.pl')
        self.assertEqual(len(serv_with_ven), 1)
        self.assertEqual(len(serv_without_ven), 0)
        # local service for tests
        service = CI(name='ceneo.pl', type=CIType.objects.get(id=7))
        service.save()
        # local venture for tests
        venture = CI(name='allegro_prod', type=CIType.objects.get(id=4))
        venture.save()
        reload_report = self.client.get(url, follow=True)
        re_serv_with_ven = reload_report.context['serv_with_ven']
        re_serv_without_ven = reload_report.context['serv_without_ven']
        self.assertEqual(len(re_serv_with_ven), 1)
        self.assertEqual(len(re_serv_without_ven), 1)


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
