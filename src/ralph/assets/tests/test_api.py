# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.models import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    ObjectModelType,
    Service,
    ServiceEnvironment
)
from ralph.assets.tests.factories import (
    CategoryFactory,
    DataCenterAssetModelFactory,
    EnvironmentFactory,
    ManufacturerFactory,
    ServiceFactory
)
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory


class ServicesEnvironmentsAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.envs = EnvironmentFactory.create_batch(2)
        self.services = ServiceFactory.create_batch(2)
        ServiceEnvironment.objects.create(
            service=self.services[0], environment=self.envs[0]
        )

    def test_get_environment(self):
        env = self.envs[0]
        url = reverse('environment-detail', args=(env.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], env.name)
        self.assertIn('url', response.data)

    def test_create_environment(self):
        url = reverse('environment-list')
        data = {
            'name': 'test-env'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'test-env')
        self.assertEqual(Environment.objects.count(), 3)

    def test_patch_environment(self):
        env = self.envs[0]
        url = reverse('environment-detail', args=(env.id,))
        data = {
            'name': 'test-env-2'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test-env-2')

    def test_get_service(self):
        service = self.services[0]
        url = reverse('service-detail', args=(service.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], service.name)
        self.assertEqual(
            response.data['environments'][0]['id'],
            service.environments.all()[0].id
        )

    def test_create_service(self):
        url = reverse('service-list')
        data = {
            'name': 'test-service',
            'environments': [self.envs[0].id, self.envs[1].id],
            'business_owners': [self.user1.id],
            'technical_owners': [self.user2.id],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        service = Service.objects.get(pk=response.data['id'])
        self.assertEqual(service.name, 'test-service')
        self.assertCountEqual(
            service.environments.values_list('id', flat=True),
            data['environments']
        )
        self.assertIn(self.user1, service.business_owners.all())
        self.assertIn(self.user2, service.technical_owners.all())

    def test_patch_service(self):
        service = self.services[1]
        url = reverse('service-detail', args=(service.id,))
        data = {
            'name': 'test-service-2',
            'environments': [self.envs[1].id],
            'technical_owners': [self.user2.id],
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.name, 'test-service-2')
        self.assertCountEqual(
            service.environments.values_list('id', flat=True),
            data['environments']
        )
        self.assertIn(self.user2, service.technical_owners.all())

    def test_get_service_environment(self):
        service_env = ServiceEnvironment.objects.all()[0]
        url = reverse('serviceenvironment-detail', args=(service_env.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service']['id'], service_env.service.id)
        self.assertEqual(
            response.data['environment']['id'], service_env.environment.id
        )

    def test_create_service_should_return_method_not_allowed(self):
        url = reverse('serviceenvironment-list')
        data = {
            'service': self.services[0].id,
            'environment': self.envs[0].id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_patch_service_should_return_method_not_allowed(self):
        service_env = ServiceEnvironment.objects.all()[0]
        url = reverse('serviceenvironment-detail', args=(service_env.id,))
        data = {
            'service': self.services[0].id,
            'environment': self.envs[0].id,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class ManufacturerAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.manufacturer = ManufacturerFactory()

    def test_get_manufacturer_list(self):
        url = reverse('manufacturer-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['name'], self.manufacturer.name
        )

    def test_get_manufacturer_details(self):
        url = reverse('manufacturer-detail', args=(self.manufacturer.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.manufacturer.name)

    def test_create_manufacturer(self):
        url = reverse('manufacturer-list')
        data = {
            'name': 'Lenovo'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Lenovo')
        self.assertEqual(Manufacturer.objects.count(), 2)

    def test_patch_manufacturer(self):
        url = reverse('manufacturer-detail', args=(self.manufacturer.id,))
        data = {
            'name': 'Lenovo'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.manufacturer.refresh_from_db()
        self.assertEqual(self.manufacturer.name, 'Lenovo')


class CategoryAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.category = CategoryFactory(name='rack-servers')

    def test_get_category_list(self):
        url = reverse('category-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['name'], self.category.name
        )

    def test_get_category_details(self):
        url = reverse('category-detail', args=(self.category.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)

    def test_create_category(self):
        url = reverse('category-list')
        data = {
            'name': 'cell-phones',
            'code': 'cp'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'cell-phones')
        self.assertEqual(Category.objects.count(), 2)
        category = Category.objects.get(pk=response.data['id'])
        self.assertEqual(category.name, 'cell-phones')
        self.assertEqual(category.code, 'cp')
        self.assertIsNone(category.parent)

    def test_create_category_with_parent(self):
        url = reverse('category-list')
        data = {
            'name': 'cell-phones',
            'parent': self.category.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'cell-phones')
        self.assertEqual(Category.objects.count(), 2)
        category = Category.objects.get(pk=response.data['id'])
        self.assertEqual(category.name, 'cell-phones')
        self.assertEqual(category.parent, self.category)

    def test_patch_category(self):
        url = reverse('category-detail', args=(self.category.id,))
        data = {
            'name': 'cell-phones'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'cell-phones')


class AssetModelAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.manufacturer = ManufacturerFactory()
        self.asset_model = DataCenterAssetModelFactory()

    def test_get_asset_model_list(self):
        url = reverse('assetmodel-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['name'], self.asset_model.name
        )

    def test_get_asset_model_details(self):
        url = reverse('assetmodel-detail', args=(self.asset_model.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.asset_model.name)

    def test_create_asset_model(self):
        url = reverse('assetmodel-list')
        data = {
            'name': 'MacBook Pro',
            'manufacturer': self.manufacturer.id,
            'type': ObjectModelType.back_office.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssetModel.objects.count(), 2)
        asset_model = AssetModel.objects.get(pk=response.data['id'])
        self.assertEqual(asset_model.name, 'MacBook Pro')
        self.assertEqual(asset_model.manufacturer, self.manufacturer)

    def test_patch_asset_model(self):
        url = reverse('assetmodel-detail', args=(self.asset_model.id,))
        data = {
            'name': 'Iphone 6'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.asset_model.refresh_from_db()
        self.assertEqual(self.asset_model.name, 'Iphone 6')


class BaseObjectAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.bo_asset = BackOfficeAssetFactory(barcode='12345')
        self.dc_asset = DataCenterAssetFactory(barcode='54321')

    def test_get_base_objects_list(self):
        url = reverse('baseobject-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        barcodes = [item['barcode'] for item in response.data['results']]
        self.assertCountEqual(barcodes, set(['12345', '54321']))

    def test_get_asset_model_details(self):
        url = reverse('baseobject-detail', args=(self.bo_asset.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barcode'], '12345')
