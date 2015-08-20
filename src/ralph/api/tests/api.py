# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from ralph.api import RalphAPISerializer, RalphAPIViewSet
from ralph.api.routers import RalphRouter
from ralph.tests.models import Foo


class FooSerializer(RalphAPISerializer):
    class Meta:
        model = Foo


class FooViewSet(RalphAPIViewSet):
    queryset = Foo.objects.all()
    serializer_class = FooSerializer

router = RalphRouter()
router.register(r'foos', FooViewSet)
urlpatterns = [
    url(r'^test-ralph-api/', include(router.urls, namespace='test-ralph-api')),
]
