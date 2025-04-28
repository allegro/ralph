from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers, serializers, viewsets

from ..api import (
    CustomFieldsFilterBackend,
    NestedCustomFieldsRouterMixin,
    WithCustomFieldsSerializerMixin,
)
from .models import SomeModel


class SomeModelSerializer(WithCustomFieldsSerializerMixin, serializers.Serializer):
    class Meta:
        model = SomeModel
        fields = ("id", "custom_fields", "configuration_variables")


class SomeModelViewset(viewsets.ModelViewSet):
    queryset = SomeModel.objects.prefetch_related("custom_fields")
    serializer_class = SomeModelSerializer
    filter_backends = viewsets.ModelViewSet.filter_backends + [
        CustomFieldsFilterBackend
    ]


class CustomFieldsAPITestsRouter(NestedCustomFieldsRouterMixin, routers.DefaultRouter):
    pass


router = CustomFieldsAPITestsRouter()
router.register(r"somemodel", SomeModelViewset)

urlpatterns = [re_path(r"^", include(router.urls))]
