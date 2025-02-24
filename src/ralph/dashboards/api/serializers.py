from ralph.api import RalphAPISerializer
from ralph.dashboards.models import Graph


class GraphSerializer(RalphAPISerializer):
    class Meta:
        model = Graph
        fields = ("name", "description", "url")


class GraphSerializerDetail(RalphAPISerializer):
    class Meta:
        model = Graph

    def to_representation(self, instance):
        return {
            "name": instance.name,
            "description": instance.description,
            "params": instance.params,
            "data": instance.get_data(),
        }
