# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.supports.models import Support


class SupportSerializer(RalphAPISerializer):
    class Meta:
        model = Support


class SupportViewSet(RalphAPIViewSet):
    queryset = Support.objects.all()
    serializer_class = SupportSerializer


router.register(r'supports', SupportViewSet)
urlpatterns = []
