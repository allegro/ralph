from django.test import TestCase

from ralph.data_center.publishers import _get_host_data
from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.virtual.tests.factories import (
    CloudHostFullFactory,
    VirtualServerFactory
)


class TestPublishing(TestCase):

    def setUp(self):
        self.cloud_host = CloudHostFullFactory()
        self.dc_asset = DataCenterAssetFullFactory()
        self.virtual_server = VirtualServerFactory()

    def test_dc_asset_is_serialized_ok(self):
        data = _get_host_data(self.dc_asset)
        self.assertTrue(isinstance(data, dict))

    def test_cloud_host_is_serialized_ok(self):
        data = _get_host_data(self.cloud_host)
        self.assertTrue(isinstance(data, dict))

    def test_virtual_server_is_serialized_ok(self):
        data = _get_host_data(self.virtual_server)
        self.assertTrue(isinstance(data, dict))

    def test_sending_data_includes_previous_data(self):
        results = []
        for obj_name in ['cloud_host', 'dc_asset', 'virtual_server']:
            data = _get_host_data(getattr(self, obj_name))
            results.append('_previous_state' in data)
        self.assertEqual(results, [True] * 3)
