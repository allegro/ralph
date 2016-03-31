# -*- coding: utf-8 -*-
from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.lib.transitions.models import Action, Transition, TransitionModel


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

    class Meta:
        model = Transition
