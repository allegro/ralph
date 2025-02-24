# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Prefetch

from ralph.accounts.models import Region, Team
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.permissions import IsSuperuserOrReadonly
from ralph.back_office.api import (
    BackOfficeAssetSimpleSerializer,
    BackOfficeAssetViewSet
)
from ralph.back_office.models import BackOfficeAsset
from ralph.licences.api import LicenceUserViewSet
from ralph.licences.api_simple import SimpleLicenceUserSerializer
from ralph.licences.models import LicenceUser


class GroupSerializer(RalphAPISerializer):
    class Meta:
        model = Group
        exclude = ("permissions",)


class GroupViewSet(RalphAPIViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class RalphUserSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "url",
            "username",
            "first_name",
            "last_name",
            "email",
            "country",
        )


class RalphUserSerializer(RalphAPISerializer):
    assets_as_user = BackOfficeAssetSimpleSerializer(read_only=True, many=True)
    assets_as_owner = BackOfficeAssetSimpleSerializer(read_only=True, many=True)
    licences = SimpleLicenceUserSerializer(read_only=True, many=True)

    class Meta:
        model = get_user_model()
        exclude = ("user_permissions", "password", "groups")
        depth = 1


class RalphUserViewSet(RalphAPIViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = RalphUserSerializer
    _assets_queryset = BackOfficeAsset.objects.select_related(
        *BackOfficeAssetViewSet.select_related
    ).prefetch_related("tags")
    prefetch_related = [
        "regions",
        "user_permissions",
        Prefetch(
            "licences",
            queryset=LicenceUser.objects.select_related(
                *LicenceUserViewSet.select_related
            ).prefetch_related("licence__tags"),
        ),
        Prefetch("assets_as_user", queryset=_assets_queryset),
        Prefetch("assets_as_owner", queryset=_assets_queryset),
    ]
    permission_classes = RalphAPIViewSet.permission_classes + [IsSuperuserOrReadonly]
    http_method_names = [m for m in RalphAPIViewSet.http_method_names if m != "post"]


class RegionSerializer(RalphAPISerializer):
    class Meta:
        model = Region
        fields = "__all__"


class RegionViewSet(RalphAPIViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class TeamSerializer(RalphAPISerializer):
    class Meta:
        model = Team
        fields = "__all__"


class TeamViewSet(RalphAPIViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


router.register(r"groups", GroupViewSet)
router.register(r"users", RalphUserViewSet)
router.register(r"regions", RegionViewSet)
router.register(r"teams", TeamViewSet)
urlpatterns = []
