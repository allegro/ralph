import logging

from rest_framework.filters import BaseFilterBackend

from ..models import WithCustomFieldsMixin

logger = logging.getLogger(__name__)


class CustomFieldsFilterBackend(BaseFilterBackend):
    """
    Filter queryset by custom fields. Multiple values for single custom field
    could ba passed in one request. To filter by some custom field, prepend it's
    attribute name by 'customfield_' in request query params, ex.
    `<URL>?customfield__myfield=1&customfield__myfield=2&customfield__otherfield=a`
    """
    prefix = 'customfield__'

    def _handle_customfield_filter(self, queryset, custom_field, value):
        logger.info(
            'Filtering by custom field {} : {}'.format(custom_field, value)
        )
        return queryset.filter(
            custom_fields__custom_field__attribute_name=custom_field,
            custom_fields__value__in=value,
        )

    def filter_queryset(self, request, queryset, view):
        if issubclass(queryset.model, WithCustomFieldsMixin):
            for key in request.query_params:
                if key.startswith(self.prefix):
                    queryset = self._handle_customfield_filter(
                        queryset,
                        key[len(self.prefix):],
                        request.query_params.getlist(key)
                    )
        return queryset
