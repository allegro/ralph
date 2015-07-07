# -*- coding: utf-8 -*-

from rest_framework import viewsets

from ralph.data_center.models.physical import (
    DataCenterAsset,
)
from ralph.data_center.serializers.models_serializer import (
    DataCenterAssetSerializer,
)


class DataCenterAssetViewSet(viewsets.ModelViewSet):
    queryset = DataCenterAsset.objects.all()
    serializer_class = DataCenterAssetSerializer
