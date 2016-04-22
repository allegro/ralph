# -*- coding: utf-8 -*-
from ralph.accounts.api_simple import SimpleRalphUserSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import ReversionHistoryAPISerializerMixin
from ralph.assets.api.serializers import BaseObjectSerializer
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


class LicenceUserSerializer(RalphAPISerializer):
    user = SimpleRalphUserSerializer()

    class Meta:
        model = LicenceUser


class BaseObjectLicenceSerializer(
    ReversionHistoryAPISerializerMixin,
    RalphAPISerializer
):

    class Meta:
        model = BaseObjectLicence

    def validate(self, data):
        base_object_licence = BaseObjectLicence(**data)
        base_object_licence.clean()
        return data


class LicenceSerializer(BaseObjectSerializer):
    base_objects = BaseObjectLicenceSerializer(
        many=True, read_only=True, source='baseobjectlicence_set'
    )
    users = LicenceUserSerializer(
        many=True, read_only=True, source='licenceuser_set'
    )

    class Meta:
        model = Licence
        depth = 1
        exclude = ('content_type', 'service_env')


class SoftwareSerializer(RalphAPISerializer):
    class Meta:
        model = Software


# ========
# VIEWSETS
# ========
class BaseObjectLicenceViewSet(RalphAPIViewSet):
    queryset = BaseObjectLicence.objects.all()
    serializer_class = BaseObjectLicenceSerializer
    select_related = [
        'licence', 'licence__region', 'licence__manufacturer',
        'licence__licence_type', 'licence__software', 'base_object'
    ]
    save_serializer_class = BaseObjectLicenceSerializer


class LicenceTypeViewSet(RalphAPIViewSet):
    queryset = LicenceType.objects.all()
    serializer_class = LicenceTypeSerializer


class LicenceViewSet(RalphAPIViewSet):
    queryset = Licence.objects.all()
    serializer_class = LicenceSerializer
    select_related = ['region', 'manufacturer', 'office_infrastructure']
    prefetch_related = [
        'tags', 'users', 'licenceuser_set__user',
        'baseobjectlicence_set__base_object',
    ]


class LicenceUserViewSet(RalphAPIViewSet):
    queryset = LicenceUser.objects.all()
    serializer_class = LicenceUserSerializer
    select_related = [
        'licence', 'licence__region', 'licence__manufacturer',
        'licence__licence_type', 'licence__software', 'user'
    ]


class SoftwareViewSet(RalphAPIViewSet):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer


router.register(r'base-objects-licences', BaseObjectLicenceViewSet)
router.register(r'licences', LicenceViewSet)
router.register(r'licence-types', LicenceTypeViewSet)
router.register(r'licence-users', LicenceUserViewSet)
router.register(r'software', SoftwareViewSet)
urlpatterns = []
