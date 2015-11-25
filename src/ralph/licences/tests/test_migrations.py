from django.contrib.contenttypes.models import ContentType
from django_migration_testcase import MigrationTest

from ralph.assets.models import BaseObject, ObjectModelType, ServiceEnvironment


class LicenceInheritingBaseObjectMigrationTest(MigrationTest):

    before = [
        ('licences', '0009_auto_20151120_1817'),
        ('assets', '0010_service_env_inherits_base_object'),
        ('accounts', '0003_auto_20151112_0920'),
        ('contenttypes', '0002_remove_content_type_name')
    ]
    after = [
        ('licences', '0010_auto_20151123_1522'),
        ('assets', '0010_service_env_inherits_base_object'),
        ('accounts', '0003_auto_20151112_0920'),
    ]

    def setUp(self):
        super().setUp()

    def test_migration(self):
        print('testing licence migration')
        # before migration
        LicenceBefore = self.get_model_before('licences.Licence')
        LicenceType = self.get_model_before('licences.LicenceType')
        Software = self.get_model_before('licences.Software')
        Region = self.get_model_before('accounts.Region')

        self.software = Software.objects.create(name='test')
        self.licence_type = LicenceType.objects.create(name='type')
        self.region = Region.objects.create(name='pl')

        self.licence = LicenceBefore.objects.create(
            licence_type=self.licence_type,
            software=self.software,
            region_id=self.region.id,
            niw='TEST',
            number_bought=10,
            remarks='test'
        )

        base_objects_count = BaseObject.objects.count()
        self.assertEqual(LicenceBefore.objects.count(), 1)
        # run migration
        self.run_migration()

        LicenceAfter = self.get_model_after('licences.Licence')

        self.assertEqual(LicenceAfter.objects.count(), 1)
        self.assertEqual(BaseObject.objects.count(), base_objects_count + 1)

        licence = LicenceAfter.objects.get(niw='TEST')
        self.assertEqual(licence.baseobject_ptr.remarks, 'test')
