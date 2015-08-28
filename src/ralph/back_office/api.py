# -*- coding: utf-8 -*-
from ralph.accounts.api import SimpleRalphUserSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import AssetSerializer
from ralph.back_office.admin import BackOfficeAssetAdmin
from ralph.back_office.models import BackOfficeAsset, Warehouse


class WarehouseSerializer(RalphAPISerializer):
    class Meta:
        model = Warehouse


class WarehouseViewSet(RalphAPIViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class BackOfficeAssetSerializer(AssetSerializer):
    user = SimpleRalphUserSerializer()
    owner = SimpleRalphUserSerializer()

    class Meta:
        model = BackOfficeAsset
        depth = 1
        exclude = ('content_type',)


class BackOfficeAssetViewSet(RalphAPIViewSet):
    select_related = BackOfficeAssetAdmin.list_select_related + [
        'service_env', 'service_env__service', 'service_env__environment',
        'user', 'owner',
    ]
    prefetch_related = [
        'user__groups', 'user__user_permissions',
        'service_env__service__environments',
        'service_env__service__business_owners',
        'service_env__service__technical_owners',
    ]
    queryset = BackOfficeAsset.objects.all()
    serializer_class = BackOfficeAssetSerializer


router.register(r'warehouses', WarehouseViewSet)
router.register(r'back-office-assets', BackOfficeAssetViewSet)
urlpatterns = []
