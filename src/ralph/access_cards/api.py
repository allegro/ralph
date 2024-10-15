from ralph.access_cards.models import AccessCard, AccessZone
from ralph.accounts.api import RalphUserSimpleSerializer, RegionSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router


class AccessZoneSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = AccessZone
        depth = 0
        fields = ["id", "name", "parent", "description"]


class AccessZoneSerializer(RalphAPISerializer):
    class Meta:
        model = AccessZone
        depth = 1
        fields = "__all__"


class AccessCardSerializer(RalphAPISerializer):
    user = RalphUserSimpleSerializer()
    owner = RalphUserSimpleSerializer()
    region = RegionSerializer()
    access_zones = AccessZoneSimpleSerializer(many=True)

    class Meta:
        model = AccessCard
        fields = [
            "id",
            "status",
            "user",
            "owner",
            "created",
            "modified",
            "visual_number",
            "system_number",
            "issue_date",
            "notes",
            "region",
            "access_zones",
        ]


class AccessCardViewSet(RalphAPIViewSet):
    queryset = AccessCard.objects.order_by("id").all()
    select_related = ["user", "owner", "region"]
    serializer_class = AccessCardSerializer
    prefetch_related = ["access_zones"]
    extended_filter_fields = {
        "access_zones__name": ["access_zones__name__icontains"],
        "access_zones__id": ["access_zones__id"],
    }


class AccessZoneViewSet(RalphAPIViewSet):
    queryset = AccessZone.objects.all()
    serializer_class = AccessZoneSerializer


router.register(r"access-card", AccessCardViewSet)
router.register(r"access-zone", AccessZoneViewSet)
urlpatterns = []
