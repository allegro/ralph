from ralph.api import router
from ralph.assets.api.views import (
    AssetModelViewSet,
    BaseObjectViewSet,
    BusinessSegmentViewSet,
    CategoryViewSet,
    EnvironmentViewSet,
    ManufacturerViewSet,
    ProfitCenterViewSet,
    ServiceEnvironmentViewSet,
    ServiceViewSet
)

router.register(r'assetmodels', AssetModelViewSet)
router.register(r'base-objects', BaseObjectViewSet)
router.register(r'business-segments', BusinessSegmentViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'environments', EnvironmentViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'profit-centers', ProfitCenterViewSet)
router.register(r'services-environments', ServiceEnvironmentViewSet)
router.register(r'services', ServiceViewSet)
urlpatterns = []
