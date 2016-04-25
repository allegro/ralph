from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, viewsets
# from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ralph.api import RalphAPISerializer, router, RalphAPIViewSet
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue


class CustomFieldsSerializerMixin(serializers.Serializer):
    custom_fields = serializers.SerializerMethodField()

    def get_custom_fields(self, obj):
        return {
            cfv.custom_field.attribute_name: cfv.value
            for cfv in obj.custom_fields.all()
        }


class CustomFieldSerializer(RalphAPISerializer):
    class Meta:
        model = CustomField
        fields = ('name', 'attribute_name', 'type', 'default_value')


class CustomFieldValueSerializer(RalphAPISerializer):
    custom_field = CustomFieldSerializer()

    class Meta:
        model = CustomFieldValue
        fields = ('custom_field', 'value', 'url')


class CustomFieldValueViewset(RalphAPIViewSet):
    queryset = CustomFieldValue.objects.all()
    serializer_class = CustomFieldValueSerializer


class ObjectCustomFieldsViewSet(viewsets.ViewSet):
# class ObjectCustomFieldsViewSet(RalphAPIViewSet):
    queryset = CustomFieldValue.objects.all()
    related_model = None
    # serializer_class = CustomFieldValueSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.related_model:
            raise Exception()  # TODO

    def list(self, request, object_pk=None):
        customfields = self.queryset.filter(
            content_type=ContentType.objects.get_for_model(self.related_model),
            object_id=object_pk,
        )
        serializer = CustomFieldValueSerializer(customfields, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None, object_pk=None):
        # TODO: get_object_or_404
        customfields = self.queryset.get(
            content_type=ContentType.objects.get_for_model(self.related_model),
            object_id=object_pk,
            pk=pk,
        )
        serializer = CustomFieldValueSerializer(customfields, context={'request': request})
        return Response(serializer.data)


router.register(r'customfieldsvalues', CustomFieldValueViewset)
urlpatterns = []
