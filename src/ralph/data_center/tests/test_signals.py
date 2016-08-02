from django.test import TestCase

from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
)
from ralph.data_center.models.physical import (
    _get_dc_asset_data,
    DataCenterAsset,
)


class TestX(TestCase):

    def setUp(self):
        self.dc_asset = DataCenterAsset()

    def test_asset_is_serialized_ok(self):
        data = _get_dc_asset_data(DataCenterAsset, self.dc_asset)
