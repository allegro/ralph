# -*- coding: utf-8 -*-

from ralph.accounts.api_simple import ExtendedRalphUserSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import ReversionHistoryAPISerializerMixin
from ralph.assets.api.serializers import (
    BaseObjectSimpleSerializer,
    ServiceEnvironmentSimpleSerializer
)
from ralph.lib.api.utils import renderer_classes_without_form
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)


# ===========
# SERIALIZERS
# ===========
class LicenceTypeSerializer(RalphAPISerializer):
    class Meta:
        model = LicenceType
        fields = "__all__"


class LicenceUserSerializer(RalphAPISerializer):
    user = ExtendedRalphUserSerializer()

    class Meta:
        model = LicenceUser
        fields = "__all__"


class BaseObjectLicenceSerializer(
    ReversionHistoryAPISerializerMixin, RalphAPISerializer
):
    class Meta:
        model = BaseObjectLicence
        fields = "__all__"

    def validate(self, data):
        base_object_licence = BaseObjectLicence(**data)
        base_object_licence.clean()
        return data


class LicenceSerializer(BaseObjectSimpleSerializer):
    base_objects = BaseObjectLicenceSerializer(
        many=True, read_only=True, source="baseobjectlicence_set"
    )
    users = LicenceUserSerializer(many=True, read_only=True, source="licenceuser_set")
    service_env = ServiceEnvironmentSimpleSerializer()

    class Meta:
        model = Licence
        depth = 1
        exclude = ("content_type", "configuration_path")


class SoftwareSerializer(RalphAPISerializer):
    class Meta:
        model = Software
        fields = "__all__"


# ========
# VIEWSETS
# ========
class BaseObjectLicenceViewSet(RalphAPIViewSet):
    renderer_classes = renderer_classes_without_form(RalphAPIViewSet.renderer_classes)
    queryset = BaseObjectLicence.objects.all()
    serializer_class = BaseObjectLicenceSerializer
    select_related = [
        "licence",
        "base_object",
        "licence__region",
        "licence__manufacturer",
        "licence__licence_type",
        "licence__software",
        "licence__budget_info",
        "licence__office_infrastructure",
        "licence__property_of",
    ]
    save_serializer_class = BaseObjectLicenceSerializer


class LicenceTypeViewSet(RalphAPIViewSet):
    queryset = LicenceType.objects.all()
    serializer_class = LicenceTypeSerializer


class LicenceViewSet(RalphAPIViewSet):
    renderer_classes = renderer_classes_without_form(RalphAPIViewSet.renderer_classes)
    queryset = Licence.objects.all()
    serializer_class = LicenceSerializer
    select_related = [
        "region",
        "manufacturer",
        "office_infrastructure",
        "licence_type",
        "software",
        "service_env",
        "service_env__service",
        "service_env__environment",
        "budget_info",
        "property_of",
    ]
    prefetch_related = [
        "tags",
        "users",
        "licenceuser_set__user",
        "baseobjectlicence_set__base_object",
        "custom_fields",
        "content_type",
    ]


class LicenceUserViewSet(RalphAPIViewSet):
    queryset = LicenceUser.objects.all()
    serializer_class = LicenceUserSerializer
    select_related = [
        "licence__region",
        "licence__manufacturer",
        "licence__office_infrastructure",
        "licence__licence_type",
        "licence__software",
        "licence__budget_info",
        "user",
    ]


class SoftwareViewSet(RalphAPIViewSet):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer


router.register(r"base-objects-licences", BaseObjectLicenceViewSet)
router.register(r"licences", LicenceViewSet)
router.register(r"licence-types", LicenceTypeViewSet)
router.register(r"licence-users", LicenceUserViewSet)
router.register(r"software", SoftwareViewSet)
urlpatterns = []
