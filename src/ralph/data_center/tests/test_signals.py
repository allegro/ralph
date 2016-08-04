from django.test import TestCase

from ralph.publishers import _get_dc_asset_data
from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.virtual.tests.factories import (
    CloudHostFullFactory,
    VirtualServerFactory,
)


class TestPublishing(TestCase):

    def setUp(self):
        self.cloud_host = CloudHostFullFactory()
        self.dc_asset = DataCenterAssetFullFactory()
        self.virtual_server = VirtualServerFactory()

    def test_dc_asset_is_serialized_ok(self):
        data = _get_dc_asset_data(self.dc_asset)

    def test_cloud_host_is_serialized_ok(self):
        data = _get_dc_asset_data(self.cloud_host)

    def test_asset_is_serialized_ok(self):
        data = _get_dc_asset_data(self.dc_asset)
