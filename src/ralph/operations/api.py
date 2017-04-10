from django.db.models import Prefetch

from ralph.accounts.api_simple import SimpleRalphUserSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.models import BaseObject
from ralph.operations.models import Operation, OperationStatus, OperationType


class OperationTypeSerializer(RalphAPISerializer):

    class Meta:
        model = OperationType
        depth = 1


class OperationStatusSerializer(RalphAPISerializer):

    class Meta:
        model = OperationStatus
        depth = 1


class OperationSerializer(RalphAPISerializer):
    type = OperationTypeSerializer()
    assignee = SimpleRalphUserSerializer()
    status = OperationStatusSerializer()

    class Meta:
        model = Operation
        depth = 1


class OperationViewSet(RalphAPIViewSet):
    queryset = Operation.objects.all().prefetch_related(
        Prefetch(
            lookup='base_objects',
            queryset=BaseObject.objects.select_related('parent')
        )
    )
    serializer_class = OperationSerializer
    select_related = ['type', 'assignee', 'status']
    filter_fields = [
        'id', 'title', 'description', 'status', 'ticket_id', 'created_date',
        'update_date', 'resolved_date', 'type__name'
    ]


class OperationTypeViewSet(RalphAPIViewSet):
    queryset = OperationType.objects.all()
    serializer_class = OperationTypeSerializer


class OperationStatusViewSet(RalphAPIViewSet):
    queryset = OperationStatus.objects.all()
    serializer_class = OperationStatusSerializer


router.register(r'operation', OperationViewSet)
router.register(r'operationtype', OperationTypeViewSet)
router.register(r'operationstatus', OperationStatusViewSet)
urlpatterns = []
