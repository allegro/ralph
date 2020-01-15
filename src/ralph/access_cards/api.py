from ralph.access_cards.models import AccessCard
from ralph.accounts.api import RalphUserSimpleSerializer
from ralph.api import RalphAPIViewSet, RalphAPISerializer, router


class AccessCardSerializer(RalphAPISerializer):
    user = RalphUserSimpleSerializer()
    owner = RalphUserSimpleSerializer()

    class Meta:
        model = AccessCard
        fields = ['id', 'status', 'user', 'owner', 'created', 'modified',
                  'visual_number', 'system_number', 'issue_date', 'notes']

class AccessCardViewSet(RalphAPIViewSet):
    queryset = AccessCard.objects.all()
    select_related = ['user', 'owner']
    serializer_class = AccessCardSerializer

router.register(r'access-card', AccessCardViewSet)
urlpatterns = []
