from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, viewsets

from ralph.api import RalphAPISerializer, RalphAPIViewSet#, router
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue


# =============================================================================
# Custom fields resources
# =============================================================================
# TODO: use generic serializer?
class CustomFieldSerializer(RalphAPISerializer):
    class Meta:
        model = CustomField
        fields = ('name', 'attribute_name', 'type', 'default_value')


class CustomFieldValueHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            'object_pk': obj.object_id,
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class CustomFieldValueSaveSerializer(RalphAPISerializer):

    class Meta:
        model = CustomFieldValue
        fields = ('id', 'custom_field', 'value')

    def __init__(self, *args, **kwargs):
        self.related_model = kwargs.pop('related_model')
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        for key in ['content_type_id', 'object_id']:
            if key in data:
                result[key] = data[key]
        return result


class CustomFieldValueSerializer(CustomFieldValueSaveSerializer):
    custom_field = CustomFieldSerializer()
    # url = CustomFieldValueHyperlinkedIdentityField()

    class Meta(CustomFieldValueSaveSerializer.Meta):
        fields = ('id', 'custom_field', 'value', 'url')

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
            # 'lookup_field': 'object_id',
            # 'lookup_url_kwarg': 'object_pk',
        }


# class CustomFieldValueViewset(RalphAPIViewSet):
#     queryset = CustomFieldValue.objects.all()
#     serializer_class = CustomFieldValueSerializer


# router.register(r'customfieldsvalues', CustomFieldValueViewset)
urlpatterns = []


# =============================================================================
# Helpers & mixins for other resources to attach custom fields
# =============================================================================
