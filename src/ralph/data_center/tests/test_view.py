from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.tests.mixins import ClientMixin, ReloadUrlsMixin


class DataCentrAssetViewTest(ClientMixin, TestCase):
    def test_changelist_view(self):
        self.login_as_user()
        DataCenterAssetFullFactory.create_batch(10)
        with self.assertNumQueries(16):
            self.client.get(
                reverse('admin:data_center_datacenterasset_changelist'),
            )

