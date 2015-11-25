from django.contrib.contenttypes.models import ContentType
from django_migration_testcase import MigrationTest

from ralph.assets.models import BaseObject, ObjectModelType, ServiceEnvironment


class ServiceEnvironmentInheritingBaseObjectMigrationTest(MigrationTest):
    app_name = 'assets'
    before = '0009_asset_property_of_rename'
    after = '0010_service_env_inherits_base_object'

    def setUp(self):
        super().setUp()

    def test_migration(self):
        print('testing service_env migration')
        # before migration
        ServiceEnvironmentBefore = self.get_model_before('ServiceEnvironment')
        self.service = self.get_model_before('Service').objects.create(
            name='test_service'
        )
        self.env = self.get_model_before('Environment').objects.create(
            name='prod'
        )
        self.env2 = self.get_model_before('Environment').objects.create(
            name='dev'
        )
        service_env = ServiceEnvironmentBefore.objects.create(
            service=self.service, environment=self.env
        )
        ServiceEnvironmentBefore.objects.create(
            service=self.service, environment=self.env2,
        )
        AssetBefore = self.get_model_before('Asset')
        AssetModelBefore = self.get_model_before('AssetModel')
        asset_model = AssetModelBefore.objects.create(
            name='XYZ', type=ObjectModelType.data_center
        )
        asset = AssetBefore.objects.create(
            service_env=service_env, force_depreciation=False, model=asset_model
        )

        self.assertEqual(ServiceEnvironmentBefore.objects.count(), 2)
        base_objects_count = BaseObject.objects.count()

        # run migration
        self.run_migration()

        # after migration
        ServiceEnvironmentAfter = self.get_model_after('ServiceEnvironment')

        self.assertEqual(ServiceEnvironmentAfter.objects.count(), 2)
        self.assertEqual(BaseObject.objects.count(), base_objects_count + 2)

        new_service_env = ServiceEnvironment.objects.get(
            service_id=self.service.id, environment_id=self.env.id
        )
        self.assertEqual(new_service_env.pk, new_service_env.baseobject_ptr_id)
        self.assertNotEqual(new_service_env.pk, service_env.id)

        asset_new = self.get_model_after('Asset').objects.get(id=asset.id)
        self.assertEqual(asset_new.service_env_id, new_service_env.pk)
        self.assertEqual(
            new_service_env.content_type,
            ContentType.objects.get_for_model(ServiceEnvironment)
        )
