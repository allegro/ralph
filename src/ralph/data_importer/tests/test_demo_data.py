from django.contrib.auth import get_user_model
from django.core import management
from django.test import TestCase

from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenterAsset


class DemoDataTestCase(TestCase):
    def test_demo_data_command(self):
        management.call_command("demodata")
        self.assertEqual(DataCenterAsset.objects.count(), 422)
        self.assertEqual(BackOfficeAsset.objects.count(), 280)
        self.assertTrue(get_user_model().objects.count() in range(32, 35))
