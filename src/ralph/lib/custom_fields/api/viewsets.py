from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_403_FORBIDDEN

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

    def _user_can_manage_customfield(self, user, custom_field):
        return (
            custom_field.managing_group is None or
            user.groups.filter(pk=custom_field.managing_group.pk).exists()
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(**self._get_related_model_info())

    def get_serializer(self, *args, **kwargs):
        kwargs['related_model'] = self.related_model
        if kwargs.get('data') is not None:
            # Make a copy so we can modify it
            # https://docs.djangoproject.com/en/2.0/ref/request-response/#django.http.QueryDict.copy
            data = kwargs['data'].copy()
            data.update(self._get_related_model_info())
            kwargs['data'] = data
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Enforce user to be in a required group for restricted custom fields.

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        custom_field = serializer.validated_data['custom_field']
        if self._user_can_manage_customfield(request.user, custom_field):
            return super().create(request, *args, **kwargs)
        else:
            return Response(status=HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """
        Enforce user to be in a required group for restricted custom fields.

        """
        custom_field = self.get_object().custom_field
        if self._user_can_manage_customfield(request.user, custom_field):
            return super().update(request, *args, **kwargs)
        else:
            return Response(status=HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """
        Enforce user to be in a required group for restricted custom fields.

        """
        custom_field = self.get_object().custom_field

        if self._user_can_manage_customfield(request.user, custom_field):
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(status=HTTP_403_FORBIDDEN)
