# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import BaseObjectLicence
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests.mixins import ClientMixin


class BaseObjectLicenceTest(ClientMixin, TestCase):

    def setUp(self):  # noqa
        super().setUp()
        self.login_as_user()
        region_pl = RegionFactory(name='pl')
        region_de = RegionFactory(name='de')
        self.licence = LicenceFactory(region=region_pl)
        self.bo_1 = BackOfficeAssetFactory(region=region_pl)
        self.bo_2 = BackOfficeAssetFactory(region=region_de)

    def test_add_base_object_licence_ok(self):
        data = {
            'baseobjectlicence_set-TOTAL_FORMS': 1,
            'baseobjectlicence_set-INITIAL_FORMS': 0,
            'baseobjectlicence_set-MIN_NUM_FORMS': 0,
            'baseobjectlicence_set-MAX_NUM_FORMS': 1000,
            'baseobjectlicence_set-0-id': '',
            'baseobjectlicence_set-0-licence': self.licence.id,
            'baseobjectlicence_set-0-base_object': self.bo_1.id,
            'baseobjectlicence_set-0-quantity': 1,
        }
        response = self.client.post(
            reverse(
                'admin:licences_licence_assignments', args=(self.licence.id,)
            ),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        base_object_licence = BaseObjectLicence.objects.filter(
            licence=self.licence, base_object=self.bo_1
        ).exists()
        self.assertTrue(base_object_licence)

    def test_add_base_object_licence_error(self):
        data = {
            'baseobjectlicence_set-TOTAL_FORMS': 1,
            'baseobjectlicence_set-INITIAL_FORMS': 0,
            'baseobjectlicence_set-MIN_NUM_FORMS': 0,
            'baseobjectlicence_set-MAX_NUM_FORMS': 1000,
            'baseobjectlicence_set-0-id': '',
            'baseobjectlicence_set-0-licence': self.licence.id,
            'baseobjectlicence_set-0-base_object': self.bo_2.id,
            'baseobjectlicence_set-0-quantity': 1,
        }
        response = self.client.post(
            reverse(
                'admin:licences_licence_assignments', args=(self.licence.id,)
            ),
            data=data,
            follow=True
        )
        self.assertContains(
            response, 'Asset region is in a different region than licence.'
        )
