from ralph.accounts.api import RalphUserSimpleSerializer
from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.serializers import RalphAPISerializer
from ralph.sim_cards.models import CellularCarrier, SIMCard, SIMCardFeatures


class CellularCarrierSerializer(RalphAPISerializer):
    class Meta:
        model = CellularCarrier
        fields = ["name"]


class SIMCardFeaturesSerializer(RalphAPISerializer):
    class Meta:
        model = SIMCardFeatures
        fields = ["name"]


class SIMCardSerializer(RalphAPISerializer):
    carrier = CellularCarrierSerializer()
    features = SIMCardFeaturesSerializer(many=True)
    user = RalphUserSimpleSerializer()
    owner = RalphUserSimpleSerializer()

    class Meta:
        model = SIMCard
        fields = [
            "status",
            "card_number",
            "phone_number",
            "pin1",
            "puk1",
            "user",
            "owner",
            "warehouse",
            "carrier",
            "features",
            "quarantine_until",
            "modified",
        ]


class CellularCarrierViewSet(RalphAPIViewSet):
    queryset = CellularCarrier.objects.all()
    serializer_class = CellularCarrierSerializer


class SIMCardFeatureViewSet(RalphAPIViewSet):
    queryset = SIMCardFeatures.objects.all()
    serializer_class = SIMCardFeaturesSerializer


class SIMCardViewSet(RalphAPIViewSet):
    queryset = SIMCard.objects.all()
    serializer_class = SIMCardSerializer
    select_related = ["carrier", "user", "owner"]
    prefetch_related = ["features"]
    filter_fields = [
        "user__username",
        "features__name",
        "owner__username",
        "carrier__name",
    ]


router.register(r"sim-card-feature", SIMCardFeatureViewSet)
router.register(r"sim-card-cellular-carrier", CellularCarrierViewSet)
router.register(r"sim-card", SIMCardViewSet)
urlpatterns = []
