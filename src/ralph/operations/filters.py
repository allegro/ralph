from ralph.admin.filters import ChoicesListFilter
from ralph.operations.models import OperationStatus


class StatusFilter(ChoicesListFilter):
    def __init__(self, *args, **kwargs):
        super(StatusFilter, self).__init__(*args, **kwargs)

        statuses = OperationStatus.objects.order_by("name")

        self._choices_list = [(status.id, status.name) for status in statuses]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        return queryset.filter(status_id=int(self.value()))
