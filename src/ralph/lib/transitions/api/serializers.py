# -*- coding: utf-8 -*-
from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.lib.transitions.conf import TRANSITION_ORIGINAL_STATUS
from ralph.lib.transitions.models import (
    Action,
    Transition,
    TransitionJob,
    TransitionModel
)


class TransitionModelSerializer(RalphAPISerializer):

    model = serializers.CharField(source='content_type.model')

    class Meta:
        model = TransitionModel
        exclude = ('content_type',)


class TransitionActionSerializer(RalphAPISerializer):

    class Meta:
        model = Action
        exclude = ('content_type',)


class TransitionSerializer(RalphAPISerializer):

    source = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = Transition

    def get_source(self, obj):
        choices = obj.model.content_type.model_class()._meta.get_field(
            obj.model.field_name
        ).choices

        return [i[1] for i in choices]

    def get_target(self, obj):
        choices = obj.model.content_type.model_class()._meta.get_field(
            obj.model.field_name
        ).choices
        if obj.target == str(TRANSITION_ORIGINAL_STATUS[0]):
            return TRANSITION_ORIGINAL_STATUS[1]
        return [i[1] for i in choices if str(i[0]) == obj.target][0]


class TransitionJobSerializer(RalphAPISerializer):

    class Meta:
        model = TransitionJob
        exclude = ('content_type',)
