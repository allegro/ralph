from ralph.api import router
from ralph.assets.api.views import (
    AssetHolderViewSet,
    AssetModelViewSet,
    BaseObjectViewSet,
    BudgetInfoViewSet,
    BusinessSegmentViewSet,
    CategoryViewSet,
    ComponentModelViewset,
    DiskShareComponentViewSet,
    DiskShareMountComponentViewSet,
    EnvironmentViewSet,
    FibreChannelComponentViewSet,
    GenericComponentViewset,
    ManufacturerViewSet,
    MemoryComponentViewSet,
    OperatingSystemComponentViewSet,
    ProcessorComponentViewSet,
    ProfitCenterViewSet,
    ServiceEnvironmentViewSet,
    ServiceViewSet,
    SoftwareComponentViewSet
)

router.register(r'assetholders', AssetHolderViewSet)
router.register(r'assetmodels', AssetModelViewSet)
router.register(r'budget-info', BudgetInfoViewSet)
router.register(r'base-objects', BaseObjectViewSet)
router.register(r'business-segments', BusinessSegmentViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'component-model', ComponentModelViewset)
router.register(r'generic-component', GenericComponentViewset)
router.register(r'environments', EnvironmentViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'profit-centers', ProfitCenterViewSet)
router.register(r'services-environments', ServiceEnvironmentViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'disk-share-component', DiskShareComponentViewSet)
router.register(r'disk-share-mount-component', DiskShareMountComponentViewSet)
router.register(r'processor-component', ProcessorComponentViewSet)
router.register(r'memory-component', MemoryComponentViewSet)
router.register(r'fibre-channel-component', FibreChannelComponentViewSet)
router.register(r'software-component', SoftwareComponentViewSet)
router.register(r'operating-system-component', OperatingSystemComponentViewSet)
urlpatterns = []
