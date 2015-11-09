# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.back_office.api import SimpleRalphUserSerializer
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)


# ==================
# SIMPLE SERIALIZERS
# ==================
class SimpleLicenceSerializer(RalphAPISerializer):
    class Meta:
        model = Licence
        depth = 1
        exclude = ('base_objects', 'users')


class SimpleLicenceUserSerializer(RalphAPISerializer):
    licence = SimpleLicenceSerializer()

    class Meta:
        model = LicenceUser


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


class BaseObjectLicenceSerializer(RalphAPISerializer):

    class Meta:
        model = BaseObjectLicence


class LicenceSerializer(RalphAPISerializer):
    base_objects = BaseObjectLicenceSerializer(
        many=True, read_only=True, source='baseobjectlicence_set'
    )
    users = LicenceUserSerializer(
        many=True, read_only=True, source='licenceuser_set'
    )

    class Meta:
        model = Licence
        depth = 1


class SoftwareSerializer(RalphAPISerializer):
    class Meta:
        model = Software


# ========
# VIEWSETS
# ========
class BaseObjectLicenceViewSet(RalphAPIViewSet):
    queryset = BaseObjectLicence.objects.all()
    serializer_class = BaseObjectLicenceSerializer


class LicenceTypeViewSet(RalphAPIViewSet):
    queryset = LicenceType.objects.all()
    serializer_class = LicenceTypeSerializer


class LicenceViewSet(RalphAPIViewSet):
    queryset = Licence.objects.all()
    serializer_class = LicenceSerializer
    select_related = ['region', 'manufacturer']
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
