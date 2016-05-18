from django.conf.urls import include, url
from rest_framework import routers, serializers, viewsets

from ..api_helpers import CustomFieldsSerializerMixin, NestedCustomFieldsRouter
from .models import SomeModel


class SomeModelSerializer(CustomFieldsSerializerMixin, serializers.Serializer):
    class Meta:
        model = SomeModel


class SomeModelViewset(viewsets.ViewSet):
    queryset = SomeModel.objects.all()
    serializer_class = SomeModelSerializer


class CustomFieldsAPITestsRouter(NestedCustomFieldsRouter, routers.DefaultRouter):
    pass


router = CustomFieldsAPITestsRouter()
router.register(r'somemodel', SomeModelViewset)

urlpatterns = [url(r'^', include(router.urls))]
