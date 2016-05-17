from django.conf.urls import include, url
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, viewsets
from rest_framework_nested.routers import NestedSimpleRouter

from .models import CustomField, CustomFieldValue
from ralph.api import RalphAPISerializer
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.api.viewsets import RalphAPIViewSet


class CustomFieldSerializer(RalphAPISerializer):
    class Meta:
        model = CustomField
        fields = ('name', 'attribute_name', 'type', 'default_value')


class CustomFieldValueHyperlinkedIdentityField(
    serializers.HyperlinkedIdentityField
):
    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            'object_pk': obj.object_id,
        }
        return self.reverse(
            view_name, kwargs=kwargs, request=request, format=format
        )


class CustomFieldSerializerMixin(object):
    class Meta:
        model = CustomFieldValue
        fields = ('id', 'url', 'custom_field', 'value')

    def __init__(self, *args, **kwargs):
        self.related_model = kwargs.pop('related_model')
        super().__init__(*args, **kwargs)

    def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        if field_name == 'url':
            field_class = CustomFieldValueHyperlinkedIdentityField
            field_kwargs = self._get_custom_field_value_url_kwargs(model_class)
        else:
            field_class, field_kwargs = super().build_url_field(
                field_name, model_class
            )
        return field_class, field_kwargs

    def _get_custom_field_value_url_kwargs(self, model_class):
        return {
            'view_name': '{}-customfields-detail'.format(
                self.related_model._meta.model_name
            ),
        }


class CustomFieldValueSaveSerializer(
    CustomFieldSerializerMixin, RalphAPISaveSerializer
):
    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        for key in ['content_type_id', 'object_id']:
            if key in data:
                result[key] = data[key]
        return result


class CustomFieldValueSerializer(
    CustomFieldSerializerMixin, RalphAPISerializer
):
    custom_field = CustomFieldSerializer()

    class Meta:
        model = CustomFieldValue
        fields = ('id', 'custom_field', 'value', 'url')


# helpers
class WithCustomFieldsSerializerMixin(serializers.Serializer):
    custom_fields = serializers.SerializerMethodField()

    def get_custom_fields(self, obj):
        return {
            cfv.custom_field.attribute_name: cfv.value
            for cfv in obj.custom_fields.all()
        }


class ObjectCustomFieldsViewSet(viewsets.ModelViewSet):
    queryset = CustomFieldValue.objects.all()
    related_model = None
    serializer_class = CustomFieldValueSerializer
    save_serializer_class = CustomFieldValueSaveSerializer
    related_model_router_lookup = 'object'
    related_model_lookup_field = 'object_id'
    related_model_url_field = 'object_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.related_model:
            raise Exception()  # TODO

    def _get_related_model_info(self):
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


class NestedCustomFieldsRouter(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nested_registry = []

    def register(self, prefix, viewset, base_name=None):
        super().register(prefix, viewset, base_name=base_name)
        if base_name is None:
            base_name = self.get_default_base_name(viewset)
        if (
            issubclass(
                viewset.serializer_class, WithCustomFieldsSerializerMixin
            ) and
            getattr(viewset, '_nested_custom_fields', True)
        ):
            self._attach_nested_custom_fields(prefix, viewset, base_name)

    def _attach_nested_custom_fields(self, prefix, viewset, base_name):
        model = viewset.queryset.model
        custom_fields_related_viewset = type(
            '{}CustomFieldsViewSet'.format(model._meta.object_name),
            (ObjectCustomFieldsViewSet, RalphAPIViewSet),
            {'related_model': model}
        )
        nested_router = NestedSimpleRouter(
            self,
            prefix,
            lookup=custom_fields_related_viewset.related_model_router_lookup
        )
        nested_router.register(
            r'customfields',
            custom_fields_related_viewset,
            base_name='{}-customfields'.format(base_name),
        )
        self.nested_registry.append(nested_router)

    def get_urls(self):
        urls = super().get_urls()
        for nr in self.nested_registry:
            urls.append(url(r'^', include(nr.urls)))
        return urls

urlpatterns = []
