from ralph.api import router
from ralph.dashboards.api.views import GraphViewSet

router.register(r"graph", GraphViewSet)

urlpatterns = []
