from django.contrib.auth import get_user_model
from django.test import TestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.models import BaseObject
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_importer.fields import ThroughField
from ralph.data_importer.widgets import (
    ManyToManyThroughWidget,
    UserManyToManyWidget
)
from ralph.licences.models import BaseObjectLicence, LicenceUser
from ralph.licences.tests.factories import LicenceFactory


class DataImporterFieldsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.back_office_assets = BackOfficeAssetFactory.create_batch(4)
        cls.users = [UserFactory() for i in range(4)]
        cls.delete_users = UserFactory.create_batch(2)
        cls.licence = LicenceFactory()
        cls.licence2 = LicenceFactory()

    def setUp(self):
        LicenceUser.objects.create(licence=self.licence, user=self.users[0])
        for user in self.delete_users:
            LicenceUser.objects.create(licence=self.licence, user=user)
        BaseObjectLicence.objects.create(
            licence=self.licence,
            base_object=self.back_office_assets[0],
        )
        BaseObjectLicence.objects.create(
            licence=self.licence,
            base_object=self.back_office_assets[1],
        )

        LicenceUser.objects.create(licence=self.licence2, user=self.users[0])
        LicenceUser.objects.create(licence=self.licence2, user=self.users[3])
        LicenceUser.objects.create(licence=self.licence2, user=self.delete_users[0])
        BaseObjectLicence.objects.create(
            licence=self.licence2,
            base_object=self.back_office_assets[1],
        )
        BaseObjectLicence.objects.create(
            licence=self.licence2,
            base_object=self.back_office_assets[2],
        )

    def test_users_through_field(self):
        field = ThroughField(
            through_model=LicenceUser,
            through_from_field_name="licence",
            through_to_field_name="user",
            attribute="users",
            column_name="users",
            widget=UserManyToManyWidget(model=get_user_model()),
        )

        self.assertEqual(self.licence.users.all().count(), 3)
        # Make sure it doesn't touch other licences
        self.assertEqual(self.licence2.users.all().count(), 3)

        # Add and remove
        with self.assertNumQueries(5):
            field.save(
                self.licence, {"users": ",".join([i.username for i in self.users])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)

        # Not remove
        users = self.users + [UserFactory()]
        with self.assertNumQueries(3):
            field.save(self.licence, {"users": ",".join([i.username for i in users])})

        self.assertEqual(self.licence.users.all().count(), 5)

        # Remove
        with self.assertNumQueries(4):
            field.save(
                self.licence, {"users": ",".join([i.username for i in users[:4]])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)

        # Update
        with self.assertNumQueries(2):
            field.save(
                self.licence, {"users": ",".join([i.username for i in users[:4]])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)

        # Make sure it doesn't touch other licences
        self.assertEqual(self.licence2.users.all().count(), 3)

    def _get_base_objects_through_field(self):
        return ThroughField(
            column_name="base_objects",
            attribute="base_objects",
            widget=ManyToManyThroughWidget(
                model=BaseObjectLicence,
                related_model=BaseObject,
                through_field="base_object",
            ),
            through_model=BaseObjectLicence,
            through_from_field_name="licence",
            through_to_field_name="base_object",
        )

    def test_through_field_only_add(self):
        field = self._get_base_objects_through_field()
        self.assertEqual(self.licence.base_objects.all().count(), 2)
        ids = [i.pk for i in self.back_office_assets]
        with self.assertNumQueries(3):
            field.save(self.licence, {"base_objects": ",".join(map(str, ids))})

        self.assertEqual(self.licence.base_objects.all().count(), 4)
        self.assertCountEqual([bo.pk for bo in self.licence.base_objects.all()], ids)
        # Make sure it doesn't touch other licences
        self.assertEqual(self.licence2.base_objects.all().count(), 2)

    def test_through_field_only_remove(self):
        field = self._get_base_objects_through_field()
        self.assertEqual(self.licence.base_objects.all().count(), 2)
        ids = [self.back_office_assets[0].pk]
        with self.assertNumQueries(4):
            field.save(self.licence, {"base_objects": ",".join(map(str, ids))})

        self.assertEqual(self.licence.base_objects.all().count(), 1)
        self.assertCountEqual([bo.pk for bo in self.licence.base_objects.all()], ids)
        # Make sure it doesn't touch other licences
        self.assertEqual(self.licence2.base_objects.all().count(), 2)

    def test_through_field_add_and_remove(self):
        field = self._get_base_objects_through_field()
        self.assertEqual(self.licence.base_objects.all().count(), 2)
        ids = [
            self.back_office_assets[1].pk,
            self.back_office_assets[2].pk,
            self.back_office_assets[3].pk,
        ]
        with self.assertNumQueries(5):
            field.save(self.licence, {"base_objects": ",".join(map(str, ids))})
        self.assertEqual(self.licence.base_objects.all().count(), 3)
        self.assertCountEqual([bo.pk for bo in self.licence.base_objects.all()], ids)
        # Make sure it doesn't touch other licences
        self.assertEqual(self.licence2.base_objects.all().count(), 2)
