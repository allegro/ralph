# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.accounts.models import Region
from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import (
    BackOfficeAssetFactory,
    WarehouseFactory
)


class BackOffieAssetAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.service_env = ServiceEnvironmentFactory()
        self.model = BackOfficeAssetModelFactory()
        self.warehouse = WarehouseFactory()
        self.bo_asset = BackOfficeAssetFactory(
            warehouse=self.warehouse,
            model=self.model,
        )
        self.bo_asset.user = self.user1
        self.bo_asset.owner = self.user2
        self.bo_asset.save()

    def test_get_back_office_assets_list(self):
        url = reverse('backofficeasset-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], BackOfficeAsset.objects.count()
        )

    def test_get_back_office_asset_details(self):
        url = reverse('backofficeasset-detail', args=(self.bo_asset.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['hostname'], self.bo_asset.hostname)
        self.assertEqual(response.data['user']['id'], self.bo_asset.user.id)
        self.assertEqual(response.data['owner']['id'], self.bo_asset.owner.id)
        self.assertEqual(
            response.data['warehouse']['id'], self.bo_asset.warehouse.id
        )
        self.assertEqual(
            response.data['model']['id'], self.bo_asset.model.id
        )

    def test_create_back_office_asset(self):
        region = Region.objects.create(name='EU')
        url = reverse('backofficeasset-list')
        data = {
            'hostname': '12345',
            'user': self.user1.id,
            'owner': self.superuser.id,
            'region': region.id,
            'warehouse': self.warehouse.id,
            'model': self.model.id,
            'service_env': self.service_env.id,
            'force_depreciation': False,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bo_asset = BackOfficeAsset.objects.get(pk=response.data['id'])
        self.assertEqual(bo_asset.hostname, '12345')
        self.assertEqual(bo_asset.user, self.user1)
        self.assertEqual(bo_asset.owner, self.superuser)
        self.assertEqual(bo_asset.region, region)
        self.assertEqual(bo_asset.warehouse, self.warehouse)
        self.assertEqual(bo_asset.service_env, self.service_env)

    def test_patch_back_office_asset(self):
        url = reverse('backofficeasset-detail', args=(self.bo_asset.id,))
        data = {
            'user': self.user2.id,
            'owner': None,
            'force_depreciation': True,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bo_asset.refresh_from_db()
        self.assertEqual(self.bo_asset.user, self.user2)
        self.assertIsNone(self.bo_asset.owner)
        self.assertTrue(self.bo_asset.force_depreciation)
