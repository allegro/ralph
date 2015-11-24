from datetime import date

from django.contrib.contenttypes.models import ContentType
from django_migration_testcase import MigrationTest

from ralph.assets.models import BaseObject, ObjectModelType, ServiceEnvironment


class SupportInheritingBaseObjectMigrationTest(MigrationTest):

    before = [
        ('supports', '0004_auto_20151119_2158'),
        ('assets', '0010_service_env_inherits_base_object'),
        ('accounts', '0003_auto_20151112_0920'),
        ('contenttypes', '0002_remove_content_type_name')
    ]
    after = [
        ('supports', '0005_auto_20151124_1049'),
        ('assets', '0010_service_env_inherits_base_object'),
    ]

    def setUp(self):
        super().setUp()

    def test_migration(self):
        print('testing supports migration')
        # before migration
        SupportBefore = self.get_model_before('supports.Support')
        Region = self.get_model_before('accounts.Region')
        self.region = Region.objects.create(name='pl')
        self.support = SupportBefore.objects.create(
            remarks='test',
            contract_id='1',
            date_to=date(2020, 12, 31),
            region_id=self.region.id
        )

        base_objects_count = BaseObject.objects.count()
        self.assertEqual(SupportBefore.objects.count(), 1)
        # run migration
        self.run_migration()

        SupportAfter = self.get_model_after('supports.Support')

        self.assertEqual(SupportAfter.objects.count(), 1)
        self.assertEqual(BaseObject.objects.count(), base_objects_count + 1)

        support = SupportAfter.objects.get(
            contract_id=self.support.contract_id
        )
        self.assertEqual(support.baseobject_ptr.remarks, 'test')
