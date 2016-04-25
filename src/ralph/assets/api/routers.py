from django.conf.urls import include, url
from rest_framework_nested import routers

from ralph.api import router
from ralph.assets.api.views import (
    AssetHolderViewSet,
    AssetModelViewSet,
    AssetModelCustomFieldsViewSet,
    BaseObjectViewSet,
    BudgetInfoViewSet,
    BusinessSegmentViewSet,
    CategoryViewSet,
    EnvironmentViewSet,
    ManufacturerViewSet,
    ProfitCenterViewSet,
    ServiceEnvironmentViewSet,
    ServiceViewSet
)

router.register(r'assetholders', AssetHolderViewSet)
router.register(r'assetmodels', AssetModelViewSet)
router.register(r'budget-info', BudgetInfoViewSet)
router.register(r'base-objects', BaseObjectViewSet)
router.register(r'business-segments', BusinessSegmentViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'environments', EnvironmentViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'profit-centers', ProfitCenterViewSet)
router.register(r'services-environments', ServiceEnvironmentViewSet)
router.register(r'services', ServiceViewSet)

nested_router = routers.NestedSimpleRouter(router, r'assetmodels', lookup='object')
nested_router.register(r'customfields', AssetModelCustomFieldsViewSet)

urlpatterns = [
    url(r'^', include(nested_router.urls)),
]
