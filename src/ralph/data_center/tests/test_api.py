# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import (
    DataCenterAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.models import (
    DataCenterAsset,
    Orientation,
    Rack,
    RackAccessory,
    RackOrientation
)
from ralph.data_center.tests.factories import (
    AccessoryFactory,
    DataCenterAssetFactory,
    RackAccessoryFactory,
    RackFactory,
    ServerRoomFactory
)


class DataCenterAssetAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.service_env = ServiceEnvironmentFactory()
        self.model = DataCenterAssetModelFactory()
        self.rack = RackFactory()
        self.dc_asset = DataCenterAssetFactory(
            rack=self.rack,
            model=self.model,
        )
        self.dc_asset.tags.add('db', 'test')

    def test_get_data_center_assets_list(self):
        url = reverse('datacenterasset-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], DataCenterAsset.objects.count()
        )

    def test_get_data_center_asset_details(self):
        url = reverse('datacenterasset-detail', args=(self.dc_asset.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['hostname'], self.dc_asset.hostname)
        self.assertEqual(
            response.data['rack']['id'], self.dc_asset.rack.id
        )
        self.assertEqual(
            response.data['model']['id'], self.dc_asset.model.id
        )

    def test_create_data_center_asset(self):
        url = reverse('datacenterasset-list')
        data = {
            'hostname': '12345',
            'model': self.model.id,
            'rack': self.rack.id,
            'service_env': self.service_env.id,
            'force_depreciation': False,
            'configuration_path': '/monitoring/www',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dc_asset = DataCenterAsset.objects.get(pk=response.data['id'])
        self.assertEqual(dc_asset.hostname, '12345')
        self.assertEqual(dc_asset.service_env, self.service_env)
        self.assertEqual(dc_asset.rack, self.rack)

    def test_create_data_center_with_tags(self):
        url = reverse('datacenterasset-list')
        data = {
            'hostname': '12345',
            'model': self.model.id,
            'rack': self.rack.id,
            'service_env': self.service_env.id,
            'force_depreciation': False,
            'configuration_path': '/monitoring/www',
            'tags': ['prod', 'db']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dc_asset = DataCenterAsset.objects.get(pk=response.data['id'])
        self.assertEqual(dc_asset.hostname, '12345')
        self.assertEqual(dc_asset.service_env, self.service_env)
        self.assertEqual(dc_asset.rack, self.rack)
        self.assertEqual(dc_asset.tags.count(), 2)

    def test_patch_data_center_asset(self):
        url = reverse('datacenterasset-detail', args=(self.dc_asset.id,))
        data = {
            'hostname': '54321',
            'force_depreciation': True,
            'tags': ['net']
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.hostname, '54321')
        self.assertTrue(self.dc_asset.force_depreciation)
        self.assertEqual(self.dc_asset.tags.count(), 1)


class RackAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.server_room = ServerRoomFactory()
        self.accessory = AccessoryFactory()
        self.rack = RackFactory(server_room=self.server_room)
        self.rack_accessory = RackAccessoryFactory(
            accessory=self.accessory, rack=self.rack
        )

    def test_get_rack_list(self):
        url = reverse('rack-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], Rack.objects.count()
        )

    def test_get_rack_details(self):
        url = reverse('rack-detail', args=(self.rack.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.rack.name)
        self.assertEqual(
            response.data['server_room']['id'], self.server_room.id
        )
        self.assertEqual(
            response.data['server_room']['data_center']['id'],
            self.server_room.data_center.id
        )
        accessory = response.data['accessories'][0]
        self.assertEqual(accessory['id'], self.rack_accessory.id)
        self.assertEqual(accessory['name'], self.rack_accessory.accessory.name)
        self.assertEqual(accessory['position'], self.rack_accessory.position)

    def test_create_rack(self):
        url = reverse('rack-list')
        data = {
            'name': 'Rack 111',
            'server_room': self.server_room.id,
            'description': 'My rack',
            'orientation': 'bottom',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack = Rack.objects.get(pk=response.data['id'])
        self.assertEqual(rack.name, 'Rack 111')
        self.assertEqual(rack.server_room, self.server_room)
        self.assertEqual(rack.description, 'My rack')
        self.assertEqual(rack.orientation, RackOrientation.bottom)

    def test_create_rack_skip_accessories(self):
        # accessories should be created directly by RackAccessory - not assigned
        # by rack since it's m2m with through table
        url = reverse('rack-list')
        data = {
            'name': 'Rack 111',
            'server_room': self.server_room.id,
            'accessories': [self.accessory.id],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack = Rack.objects.get(pk=response.data['id'])
        self.assertEqual(rack.accessories.count(), 0)

    def test_patch_rack(self):
        url = reverse('rack-detail', args=(self.rack.id,))
        data = {
            'name': 'Rack 222',
            'description': 'qwerty',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rack.refresh_from_db()
        self.assertEqual(self.rack.name, 'Rack 222')
        self.assertEqual(self.rack.description, 'qwerty')


class RackAccessoryAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.server_room = ServerRoomFactory()
        self.accessory = AccessoryFactory()
        self.rack = RackFactory(server_room=self.server_room)
        self.rack_accessory = RackAccessoryFactory(
            accessory=self.accessory, rack=self.rack
        )

    def test_get_rack_accessory_list(self):
        url = reverse('rackaccessory-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], RackAccessory.objects.count()
        )

    def test_get_rack_accessory_details(self):
        url = reverse('rackaccessory-detail', args=(self.rack_accessory.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data['rack'].endswith(
                reverse('rack-detail', args=(self.rack_accessory.rack.id,))
            )
        )
        self.assertTrue(
            response.data['accessory'].endswith(
                reverse(
                    'accessory-detail', args=(self.rack_accessory.accessory.id,)
                )
            )
        )
        self.assertEqual(
            response.data['orientation'],
            Orientation.name_from_id(self.rack_accessory.orientation)
        )
        self.assertEqual(
            response.data['position'], self.rack_accessory.position,
        )

    def test_create_rack_accessory(self):
        url = reverse('rackaccessory-list')
        data = {
            'rack': self.rack.id,
            'accessory': self.accessory.id,
            'orientation': 'front',
            'position': 11,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack_accessory = RackAccessory.objects.get(pk=response.data['id'])
        self.assertEqual(rack_accessory.rack, self.rack)
        self.assertEqual(rack_accessory.accessory, self.accessory)
        self.assertEqual(rack_accessory.orientation, Orientation.front.id)
        self.assertEqual(rack_accessory.position, 11)

    def test_patch_rack_accessory(self):
        url = reverse('rackaccessory-detail', args=(self.rack_accessory.id,))
        data = {
            'remarks': 'qwerty',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rack_accessory.refresh_from_db()
        self.assertEqual(self.rack_accessory.remarks, 'qwerty')
