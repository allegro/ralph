# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

from rest_framework import serializers

from ralph.lib.permissions.api import (
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin
)

logger = logging.getLogger(__name__)


class ReversedChoiceField(serializers.ChoiceField):
    """
    Choice field serializer which allow to pass value by name instead of key.
    Additionally it present value in user-friendly format by-name.

    Notice that requirement for this field to work properly is uniqueness of
    choice values.

    This field works perfectly with `dj.choices.Choices`.
    """
    def __init__(self, choices, **kwargs):
        super(ReversedChoiceField, self).__init__(choices, **kwargs)
        # mapping by value
        self.reversed_choices = OrderedDict([(v, k) for (k, v) in choices])

    def to_representation(self, obj):
        """
        Return choice name (value) instead of default key.
        """
        return self.choices[obj]

    def to_internal_value(self, data):
        """
        Try to get choice by value first. If it doesn't succeed fallback to
        default action (get by key).
        """
        try:
            return self.reversed_choices[data]
        except KeyError:
            pass
        return super(ReversedChoiceField, self).to_internal_value(data)


class RalphAPISerializerMixin(
    RelatedObjectsPermissionsSerializerMixin,
    PermissionsPerFieldSerializerMixin,
):
    """
    Mix used in Ralph API serializers features:
        * checking if user has permissions to related objects (through
          `RelatedObjectsPermissionsSerializerMixin`)
        * handling field-level permissions (through
          `PermissionsPerFieldSerializerMixin`)
        * use `ReversedChoiceField` as default serializer for choice field
        * request and user object easily accessible in serializer
    """
    serializer_choice_field = ReversedChoiceField
    # turn if on when all models are linked
    # serializer_related_field = serializers.HyperlinkedRelatedField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context['request']
        self._user = self._request.user


class RalphAPISerializer(RalphAPISerializerMixin, serializers.ModelSerializer):
    pass
