# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.accounts.tests.factories import RegionFactory
from ralph.api.tests._base import RalphAPITestCase
from ralph.networks.models import IPAddress


class IPAddressAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.licence1, self.licence2 = LicenceFactory.create_batch(2)
        region_pl = RegionFactory(name='pl')
        self.licence3 = LicenceFactory(region=region_pl)
        self.base_object = BackOfficeAssetFactory()
        self.base_object2 = BackOfficeAssetFactory(region=region_pl)
        LicenceUser.objects.create(licence=self.licence1, user=self.user1)
        BaseObjectLicence.objects.create(
            licence=self.licence2, base_object=self.base_object
        )
