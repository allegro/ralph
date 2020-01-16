from ralph.access_cards.models import AccessCard
from ralph.accounts.api import RalphUserSimpleSerializer, RegionSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router


class AccessCardSerializer(RalphAPISerializer):
    user = RalphUserSimpleSerializer()
    owner = RalphUserSimpleSerializer()
    region = RegionSerializer()

    class Meta:
        model = AccessCard
        fields = ['id', 'status', 'user', 'owner', 'created', 'modified',
                  'visual_number', 'system_number', 'issue_date', 'notes',
                  'region']


class AccessCardViewSet(RalphAPIViewSet):
    queryset = AccessCard.objects.order_by('id').all()
    select_related = ['user', 'owner', 'region']
    serializer_class = AccessCardSerializer


router.register(r'access-card', AccessCardViewSet)
urlpatterns = []
