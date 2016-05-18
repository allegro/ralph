from django.conf.urls import include, url
from rest_framework import routers, serializers, viewsets

from ..api import (
    CustomFieldsFilterBackend,
    WithCustomFieldsSerializerMixin
)
from ..api.routers import NestedCustomFieldsRouterMixin
from .models import SomeModel


class SomeModelSerializer(
    WithCustomFieldsSerializerMixin, serializers.Serializer
):
    class Meta:
        model = SomeModel


class SomeModelViewset(viewsets.ModelViewSet):
    queryset = SomeModel.objects.all()
    serializer_class = SomeModelSerializer
    filter_backends = (
        viewsets.ModelViewSet.filter_backends + [CustomFieldsFilterBackend]
    )


class CustomFieldsAPITestsRouter(
    NestedCustomFieldsRouterMixin, routers.DefaultRouter
):
    pass


router = CustomFieldsAPITestsRouter()
router.register(r'somemodel', SomeModelViewset)

urlpatterns = [url(r'^', include(router.urls))]
