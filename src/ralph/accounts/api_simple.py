# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from ralph.api import RalphAPISerializer


class SimpleRalphUserSerializer(RalphAPISerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "url", "username", "first_name", "last_name")
        read_only_fields = fields
        depth = 1


class ExtendedSimpleRalphUserSerializer(SimpleRalphUserSerializer):
    class Meta:
        model = get_user_model()
        fields = SimpleRalphUserSerializer.Meta.fields + ("department", "company")


class ExtendedRalphUserSerializer(ExtendedSimpleRalphUserSerializer):
    class Meta:
        model = get_user_model()
        fields = ExtendedSimpleRalphUserSerializer.Meta.fields + ("manager", "email")
