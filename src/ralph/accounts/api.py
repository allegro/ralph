# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from ralph.accounts.models import Region
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.permissions import IsSuperuserOrReadonly


class RalphUserSerializer(RalphAPISerializer):
    class Meta:
        model = get_user_model()
        exclude = ('user_permissions', 'password')
        depth = 1


class SimpleRalphUserSerializer(RalphUserSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'url', 'username', 'first_name', 'last_name')
        read_only_fields = fields


class RalphUserViewSet(RalphAPIViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = RalphUserSerializer
    prefetch_related = ['groups', 'regions', 'user_permissions']
    permission_classes = RalphAPIViewSet.permission_classes + [
        IsSuperuserOrReadonly
    ]
    http_method_names = [
        m for m in RalphAPIViewSet.http_method_names if m != 'post'
    ]


class RegionSerializer(RalphAPISerializer):
    class Meta:
        model = Region


class RegionViewSet(RalphAPIViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


router.register(r'users', RalphUserViewSet)
router.register(r'regions', RegionViewSet)
urlpatterns = []
