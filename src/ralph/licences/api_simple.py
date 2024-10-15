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
        exclude = (
            "base_objects",
            "users",
            "content_type",
            "service_env",
            "parent",
            "configuration_path",
        )


# FIXME
del SimpleLicenceSerializer._declared_fields["tags"]


class SimpleLicenceUserSerializer(RalphAPISerializer):
    licence = SimpleLicenceSerializer()

    class Meta:
        model = LicenceUser
        fields = "__all__"


class SimpleBaseObjectLicenceSerializer(RalphAPISerializer):
    licence = SimpleLicenceSerializer()

    class Meta:
        model = BaseObjectLicence
        fields = "__all__"
