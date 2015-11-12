# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer
from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser


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


class SimpleBaseObjectLicenceSerializer(RalphAPISerializer):
    licence = SimpleLicenceSerializer()

    class Meta:
        model = BaseObjectLicence
