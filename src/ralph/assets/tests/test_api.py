# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.accounts.tests.factories import TeamFactory
from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.models import (
    AssetModel,
    BaseObject,
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
    ProfitCenterFactory,
    ServiceEnvironmentFactory,
    ServiceFactory
)
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models import Cluster, Database, DataCenterAsset, VIP
from ralph.data_center.tests.factories import (
    ClusterFactory,
    DatabaseFactory,
    DataCenterAssetFactory,
    VIPFactory
)
from ralph.domains.models import Domain
from ralph.domains.tests.factories import DomainFactory
from ralph.licences.models import Licence
from ralph.licences.tests.factories import LicenceFactory
from ralph.supports.models import Support
from ralph.supports.tests.factories import SupportFactory
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    VirtualServer
)
from ralph.virtual.tests.factories import (
    CloudFlavorFactory,
    CloudHostFactory,
    CloudProjectFactory,
    VirtualServerFactory
)


class ServicesEnvironmentsAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.envs = EnvironmentFactory.create_batch(2)
        self.services = ServiceFactory.create_batch(2)
        ServiceEnvironment.objects.create(
            service=self.services[0], environment=self.envs[0]
        )
        self.team = TeamFactory()
        self.profit_center = ProfitCenterFactory()

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
            'support_team': self.team.id,
            'profit_center': self.profit_center.id,
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
        self.assertEqual(service.profit_center, self.profit_center)
        self.assertEqual(service.support_team, self.team)

    def test_create_service_with_names_instead_of_ids(self):
        url = reverse('service-list')
        data = {
            'name': 'test-service',
            'environments': [self.envs[0].name, self.envs[1].name],
            'business_owners': [self.user1.username],
            'technical_owners': [self.user2.username],
            'support_team': self.team.name,
            'profit_center': self.profit_center.name,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        service = Service.objects.get(pk=response.data['id'])
        self.assertEqual(service.name, 'test-service')
        self.assertCountEqual(
            service.environments.values_list('name', flat=True),
            data['environments']
        )
        self.assertIn(self.user1, service.business_owners.all())
        self.assertIn(self.user2, service.technical_owners.all())
        self.assertEqual(service.profit_center, self.profit_center)
        self.assertEqual(service.support_team, self.team)

    def test_create_service_with_nulls(self):
        url = reverse('service-list')
        data = {
            'name': 'test-service',
            'environments': [self.envs[0].name, self.envs[1].name],
            'business_owners': [self.user1.username],
            'technical_owners': [self.user2.username],
            'support_team': None,
            'profit_center': None,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        service = Service.objects.get(pk=response.data['id'])
        self.assertEqual(service.name, 'test-service')
        self.assertCountEqual(
            service.environments.values_list('name', flat=True),
            data['environments']
        )
        self.assertIn(self.user1, service.business_owners.all())
        self.assertIn(self.user2, service.technical_owners.all())
        self.assertIsNone(service.profit_center)
        self.assertIsNone(service.support_team, self.team)

    def test_create_service_with_without_profit_center_and_support_team(self):
        url = reverse('service-list')
        data = {
            'name': 'test-service',
            'environments': [self.envs[0].name, self.envs[1].name],
            'business_owners': [self.user1.username],
            'technical_owners': [self.user2.username],
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        service = Service.objects.get(pk=response.data['id'])
        self.assertEqual(service.name, 'test-service')
        self.assertCountEqual(
            service.environments.values_list('name', flat=True),
            data['environments']
        )
        self.assertIn(self.user1, service.business_owners.all())
        self.assertIn(self.user2, service.technical_owners.all())
        self.assertIsNone(service.profit_center)
        self.assertIsNone(service.support_team, self.team)

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

    def test_patch_service_keep_environments_when_not_in_request(self):
        """
        Check if ServiceEnvironment for service are not cleaned after PATCH
        without environments fields.
        """
        service = self.services[0]
        environments_ids = [env.id for env in service.environments.all()]
        service_env_ids = [
            se.id for se in service.serviceenvironment_set.all()
        ]
        url = reverse('service-detail', args=(service.id,))
        data = {
            'name': 'test-service-2',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.name, 'test-service-2')
        new_environments_ids = [env.id for env in service.environments.all()]
        new_service_env_ids = [
            se.id for se in service.serviceenvironment_set.all()
        ]
        self.assertCountEqual(environments_ids, new_environments_ids)
        self.assertCountEqual(service_env_ids, new_service_env_ids)

    def test_patch_service_keep_environments_ids(self):
        """
        Check if ServiceEnvironment ids are kept after PATCH.
        """
        service = self.services[0]
        environments_ids = [env.id for env in service.environments.all()]
        service_env_ids = [
            se.id for se in service.serviceenvironment_set.all()
        ]
        url = reverse('service-detail', args=(service.id,))
        data = {
            'name': 'test-service-2',
            'environments': environments_ids,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.name, 'test-service-2')
        new_environments_ids = [env.id for env in service.environments.all()]
        new_service_env_ids = [
            se.id for se in service.serviceenvironment_set.all()
        ]
        self.assertCountEqual(environments_ids, new_environments_ids)
        self.assertCountEqual(service_env_ids, new_service_env_ids)

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


BASE_OBJECTS_FACTORIES = {
        BackOfficeAsset: BackOfficeAssetFactory,
        CloudFlavor: CloudFlavorFactory,
        CloudHost: CloudHostFactory,
        CloudProject: CloudProjectFactory,
        Database: DatabaseFactory,
        DataCenterAsset: DataCenterAssetFactory,
        Domain: DomainFactory,
        Licence: LicenceFactory,
        ServiceEnvironment: ServiceEnvironmentFactory,
        Support: SupportFactory,
        VIP: VIPFactory,
        VirtualServer: VirtualServerFactory,
        Cluster: ClusterFactory
}


class BaseObjectAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.bo_asset = BackOfficeAssetFactory(
            barcode='12345', hostname='host1'
        )
        self.bo_asset.tags.add('tag1')
        self.dc_asset = DataCenterAssetFactory(
            barcode='12543', price='10.00'
        )
        self.dc_asset.tags.add('tag2')

    def test_get_base_objects_list(self):
        url = reverse('baseobject-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        barcodes = [item['barcode'] for item in response.data['results']]
        self.assertCountEqual(barcodes, set(['12345', '12543']))

    def test_get_asset_model_details(self):
        url = reverse('baseobject-detail', args=(self.bo_asset.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barcode'], '12345')

    def test_icontains_polymorphic(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                {'hostname__icontains': 'host'}
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 1)

    def test_icontains_polymorphic_with_extended_filters(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                {'name__startswith': 'host'}
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 1)

    def test_startswith_polymorphic_different_types(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                {'barcode__startswith': '12'}
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 2)

    def test_lte_polymorphic(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                {'price__lte': '1'}
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 2)

    def test_is_lookup_used(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                {'hostname__icontains': 'no_exists_host'}
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 0)

    def test_tags(self):
        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode(
                [
                    ('tag', 'tag1'), ('tag', 'tag2')
                ]
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 0)

        url = '{}?{}'.format(
            reverse('baseobject-list'), urlencode([('tag', 'tag1')])
        )
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['results']), 1)

    def test_str_field(self):
        count = 0
        for descendant in BaseObject._polymorphic_descendants:
            if not descendant._polymorphic_descendants:
                count += 1
                obj = BASE_OBJECTS_FACTORIES[descendant]()
                url = reverse('baseobject-detail', args=(obj.id,))
                response = self.client.get(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    response.data.get('__str__'),
                    '{}: {}'.format(obj._meta.verbose_name, str(obj)),
                    msg='__str__ not found (or different) for {}'.format(
                        descendant
                    )
                )
        self.assertEqual(count, len(BASE_OBJECTS_FACTORIES))
