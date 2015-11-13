# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError

from ralph.accounts.tests.factories import RegionFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import BaseObjectLicence
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests import RalphTestCase


class BaseObjectLicenceCleanTest(RalphTestCase):

    def setUp(self):
        super().setUp()
        self.region_pl = RegionFactory(name='pl')
        self.region_de = RegionFactory(name='de')
        self.licence_de = LicenceFactory(region=self.region_de)
        self.bo_asset = BackOfficeAssetFactory(region=self.region_pl)

    def test_region_validate(self):
        base_object_licence = BaseObjectLicence()
        base_object_licence.licence = self.licence_de
        base_object_licence.base_object = self.bo_asset
        with self.assertRaisesRegex(
            ValidationError,
            (
                'Asset region is in a different region than licence.'
            )
        ):
            base_object_licence.clean()
