from ralph.api import router
from ralph.assets.api.views import (
    AssetHolderViewSet,
    AssetModelViewSet,
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
urlpatterns = []
