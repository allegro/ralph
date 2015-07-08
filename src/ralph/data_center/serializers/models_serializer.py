# -*- coding: utf-8 -*-
from rest_framework import serializers

from ralph.data_center.models.physical import (
    DataCenterAsset,
)


class DataCenterAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterAsset
        depth = 1
