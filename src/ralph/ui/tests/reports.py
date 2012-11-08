# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from ralph.cmdb.models_ci import CI, CIType, CILayer
from ralph.ui.tests.helper import login_as_su

SERVICES = {

}

class TestRaports(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.service1 = CI(
            name='allegro.pl',
            type=CIType.objects.get(id=7),
            layers=CILayer.objects.get(id=7),
        ).save()

    def test_user_login(self):
        self.assertTrue(self.client)

    def test_raports_devices(self):
        self.assertEqual(self.service1.name, 'allegro.pl')
        ci_db = CI.objects.get(id=self.service1)
        self.assertEqual(ci_db.name, self.service1.name)
