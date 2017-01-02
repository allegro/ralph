from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router

from ..models import CustomField


class CustomFieldChoicesField(serializers.Field):
    def to_representation(self, obj):
        return obj.split('|')

    def to_internal_value(self, data):
        if not isinstance(data, list):
            msg = 'Incorrect type. Expected a list, but got %s'
            raise serializers.ValidationError(msg % type(data).__name__)
        return '|'.join(data)


class CustomFieldSerializer(RalphAPISerializer):
    choices = CustomFieldChoicesField()

    class Meta:
        model = CustomField
        fields = (
            'name', 'attribute_name', 'type', 'default_value', 'choices',
            'use_as_configuration_variable', 'url'
        )


class CustomFieldViewSet(RalphAPIViewSet):
    serializer_class = CustomFieldSerializer
    save_serializer_class = CustomFieldSerializer
    queryset = CustomField.objects.all()


router.register(r'custom-fields', CustomFieldViewSet)
urlpatterns = []
