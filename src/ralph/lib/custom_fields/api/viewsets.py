from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets

from ..models import CustomFieldValue
from .serializers import (
    CustomFieldValueSaveSerializer,
    CustomFieldValueSerializer
)


class ObjectCustomFieldsViewSet(viewsets.ModelViewSet):
    """
    Mixin viewset for nested custom fields resource.
    """
    queryset = CustomFieldValue.objects.all()
    # related model in current context
    related_model = None
    serializer_class = CustomFieldValueSerializer
    save_serializer_class = CustomFieldValueSaveSerializer
    # lookup name used by rest_framework_nested
    related_model_router_lookup = 'object'
    # lookup field by related model in CustomFieldValue
    related_model_lookup_field = 'object_id'
    # name of related model in url pattern
    related_model_url_field = 'object_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.related_model is not None

    def _get_related_model_info(self):
        """
        Return filter params for related model (in current request context)
        """
        info = {
            'content_type_id': ContentType.objects.get_for_model(
                self.related_model
            ).id,
            self.related_model_lookup_field: (
                self.kwargs[self.related_model_url_field]
            )
        }
        return info

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(**self._get_related_model_info())

    def get_serializer(self, *args, **kwargs):
        kwargs['related_model'] = self.related_model
        if kwargs.get('data') is not None:
            kwargs['data'].update(self._get_related_model_info())
        return super().get_serializer(*args, **kwargs)

