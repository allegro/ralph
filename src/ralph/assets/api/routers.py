from ralph.api import router
from ralph.assets.api.views import (
    AssetHolderViewSet,
    AssetModelViewSet,
    BaseObjectViewSet,
    BudgetInfoViewSet,
    BusinessSegmentViewSet,
    CategoryViewSet,
    ConfigurationClassViewSet,
    ConfigurationModuleViewSet,
    DCHostViewSet,
    DiskViewSet,
    EnvironmentViewSet,
    EthernetViewSet,
    FibreChannelCardViewSet,
    ManufacturerKindViewSet,
    ManufacturerViewSet,
    MemoryViewSet,
    ProcessorViewSet,
    ProfitCenterViewSet,
    ServiceEnvironmentViewSet,
    ServiceViewSet
)

router.register(r"assetholders", AssetHolderViewSet)
router.register(r"assetmodels", AssetModelViewSet)
router.register(r"budget-info", BudgetInfoViewSet)
router.register(r"base-objects", BaseObjectViewSet)
router.register(r"business-segments", BusinessSegmentViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"configuration-modules", ConfigurationModuleViewSet)
router.register(r"configuration-classes", ConfigurationClassViewSet)
router.register(r"disks", DiskViewSet)
router.register(r"environments", EnvironmentViewSet)
router.register(r"fibre-channel-cards", FibreChannelCardViewSet)
router.register(r"ethernets", EthernetViewSet)
router.register(r"memory", MemoryViewSet)
router.register(r"manufacturers", ManufacturerViewSet)
router.register(r"manufacturer-kind", ManufacturerKindViewSet)
router.register(r"processors", ProcessorViewSet)
router.register(r"profit-centers", ProfitCenterViewSet)
router.register(r"services-environments", ServiceEnvironmentViewSet)
router.register(r"services", ServiceViewSet)
router.register(r"dc-hosts", DCHostViewSet, basename="dchost")

urlpatterns = []
