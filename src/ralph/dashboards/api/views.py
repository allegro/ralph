from rest_framework.viewsets import ReadOnlyModelViewSet

from ralph.dashboards.api.serializers import (
    GraphSerializer,
    GraphSerializerDetail
)
from ralph.dashboards.models import Graph


class GraphViewSet(ReadOnlyModelViewSet):
    queryset = Graph.objects.filter(active=True)
    serializer_class = GraphSerializer
    detail_serializer_class = GraphSerializerDetail

    def get_serializer_class(self):
        if self.action == "retrieve":
            return self.detail_serializer_class
        return super().get_serializer_class()
