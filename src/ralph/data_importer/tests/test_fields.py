from django.contrib.auth import get_user_model
from django.test import TestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.data_importer.fields import ThroughField
from ralph.data_importer.resources import LicenceResource
from ralph.data_importer.widgets import UserManyToManyWidget
from ralph.licences.models import Licence, LicenceUser
from ralph.licences.tests.factories import LicenceFactory


class DataImporterFieldsTestCase(TestCase):
    def setUp(self):  # noqa
        self.licence = LicenceFactory()
        self.users = [UserFactory() for i in range(4)]
        LicenceUser.objects.create(
            licence=self.licence, user=self.users[0]
        )
        for username in ['delete_user', 'delete_user2']:
            LicenceUser.objects.create(
                licence=self.licence, user=UserFactory(username=username)
            )

    def test_through_field(self):
        field = ThroughField(
            through_model=LicenceUser,
            through_from_field_name='licence',
            through_to_field_name='user',
            attribute='users',
            column_name='users',
            widget=UserManyToManyWidget(model=get_user_model())
        )

        self.assertEqual(self.licence.users.all().count(), 3)

        # Add and remove
        with self.assertNumQueries(4):
            field.save(
                self.licence,
                {'users': ','.join([i.username for i in self.users])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)

        # Not remove
        users = self.users + [UserFactory()]
        with self.assertNumQueries(3):
            field.save(
                self.licence,
                {'users': ','.join([i.username for i in users])}
            )

        self.assertEqual(self.licence.users.all().count(), 5)

        # Remove
        with self.assertNumQueries(3):
            field.save(
                self.licence,
                {'users': ','.join([i.username for i in users[:4]])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)

        # Update
        with self.assertNumQueries(2):
            field.save(
                self.licence,
                {'users': ','.join([i.username for i in users[:4]])}
            )

        self.assertEqual(self.licence.users.all().count(), 4)
