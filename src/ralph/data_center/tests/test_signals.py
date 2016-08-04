from django.test import TestCase

from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
)
from ralph.data_center.models.physical import (
    _get_dc_asset_data,
    DataCenterAsset,
)


class TestX(TestCase):

    def setUp(self):
        self.dc_asset = DataCenterAssetFullFactory()

    def test_asset_is_serialized_ok(self):
        data = _get_dc_asset_data(self.dc_asset)
