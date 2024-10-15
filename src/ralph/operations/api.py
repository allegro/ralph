from django.db.models import Prefetch
from rest_framework.serializers import SlugRelatedField

from ralph.accounts.models import RalphUser
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.models import BaseObject
from ralph.lib.api.utils import renderer_classes_without_form
from ralph.operations.models import Operation, OperationStatus, OperationType


class OperationTypeSerializer(RalphAPISerializer):
    class Meta:
        model = OperationType
        depth = 1
        fields = "__all__"


class OperationStatusSerializer(RalphAPISerializer):
    class Meta:
        model = OperationStatus
        depth = 1
        fields = "__all__"


class OperationSerializer(RalphAPISerializer):
    type = SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="name",
        queryset=OperationType.objects.all(),
    )
    assignee = SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="username",
        queryset=RalphUser.objects.all(),
    )
    reporter = SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="username",
        queryset=RalphUser.objects.all(),
    )
    status = SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="name",
        queryset=OperationStatus.objects.all(),
    )

    class Meta:
        model = Operation
        depth = 1
        fields = "__all__"


class OperationViewSet(RalphAPIViewSet):
    renderer_classes = renderer_classes_without_form(RalphAPIViewSet.renderer_classes)
    queryset = Operation.objects.all().prefetch_related(
        Prefetch(
            lookup="base_objects", queryset=BaseObject.objects.select_related("parent")
        )
    )
    serializer_class = OperationSerializer
    save_serializer_class = OperationSerializer
    select_related = ["type", "assignee", "reporter", "status"]
    prefetch_related = ["tags", "base_objects__tags"]
    filter_fields = [
        "id",
        "title",
        "description",
        "status",
        "status",
        "ticket_id",
        "created_date",
        "update_date",
        "resolved_date",
        "type",
        "assignee",
        "reporter",
    ]


class OperationTypeViewSet(RalphAPIViewSet):
    queryset = OperationType.objects.all()
    serializer_class = OperationTypeSerializer


class OperationStatusViewSet(RalphAPIViewSet):
    queryset = OperationStatus.objects.all()
    serializer_class = OperationStatusSerializer


router.register(r"operation", OperationViewSet)
router.register(r"operationtype", OperationTypeViewSet)
router.register(r"operationstatus", OperationStatusViewSet)
urlpatterns = []
