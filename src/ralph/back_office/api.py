# -*- coding: utf-8 -*-
from ralph.accounts.api_simple import SimpleRalphUserSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import AssetSerializer
from ralph.assets.api.views import BaseObjectViewSet
from ralph.back_office.admin import BackOfficeAssetAdmin
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)


class WarehouseSerializer(RalphAPISerializer):
    class Meta:
        model = Warehouse


class WarehouseViewSet(RalphAPIViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class OfficeInfrastructureSerializer(RalphAPISerializer):
    class Meta:
        model = OfficeInfrastructure


class OfficeInfrastructureViewSet(RalphAPIViewSet):
    queryset = OfficeInfrastructure.objects.all()
    serializer_class = OfficeInfrastructureSerializer


class BackOfficeAssetSimpleSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = BackOfficeAsset
        exclude = AssetSerializer.Meta.exclude + ('licences', )
        depth = 0


class BackOfficeAssetSerializer(AssetSerializer):
    user = SimpleRalphUserSerializer()
    owner = SimpleRalphUserSerializer()

    class Meta(AssetSerializer.Meta):
        model = BackOfficeAsset
        depth = 2


class BackOfficeAssetViewSet(RalphAPIViewSet):
    select_related = BackOfficeAssetAdmin.list_select_related + [
        'service_env', 'service_env__service', 'service_env__environment',
        'user', 'owner', 'property_of', 'office_infrastructure',
        'budget_info'
    ]
    prefetch_related = BaseObjectViewSet.prefetch_related + [
        'user__groups', 'user__user_permissions',
        'service_env__service__environments',
        'service_env__service__business_owners',
        'service_env__service__technical_owners',
        'tags',
    ]
    queryset = BackOfficeAsset.objects.all()
    serializer_class = BackOfficeAssetSerializer


router.register(r'warehouses', WarehouseViewSet)
router.register(r'office-infrastructures', OfficeInfrastructureViewSet)
router.register(r'back-office-assets', BackOfficeAssetViewSet)
urlpatterns = []
