# -*- coding: utf-8 -*-
from django import forms
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ralph.api import RalphReadOnlyAPIViewSet
from ralph.lib.transitions.api.serializers import (
    TransitionActionSerializer,
    TransitionModelSerializer,
    TransitionSerializer
)
from ralph.lib.transitions.models import (
    Action,
    run_transition,
    Transition,
    TransitionModel
)
from ralph.lib.transitions.views import collect_actions

FIELD_MAP = {
    forms.CharField: (serializers.CharField, [
        'max_length', 'initial', 'required'
    ]),
    forms.BooleanField: (serializers.BooleanField, ['initial', 'required']),
    forms.URLField: (serializers.URLField, ['initial', 'required']),
    forms.IntegerField: (serializers.IntegerField, ['initial', 'required']),
    forms.DecimalField: (serializers.DecimalField, ['initial', 'required']),
    forms.DateField: (serializers.DateField, ['initial', 'required']),
    forms.DateTimeField: (serializers.DateTimeField, ['initial', 'required']),
    forms.TimeField: (serializers.TimeField, ['initial', 'required']),
    forms.ModelMultipleChoiceField: (serializers.MultipleChoiceField, [
        'initial', 'required', 'choices'
    ]),
    forms.ModelChoiceField: (serializers.ChoiceField, [
        'initial', 'required', 'choices'
    ]),
}


class TransitionModelViewSet(RalphReadOnlyAPIViewSet):
    queryset = TransitionModel.objects.all()
    serializer_class = TransitionModelSerializer
    select_related = ['content_type']


class TransitionActionViewSet(RalphReadOnlyAPIViewSet):
    queryset = Action.objects.all()
    serializer_class = TransitionActionSerializer


class TransitionViewSet(RalphReadOnlyAPIViewSet):
    queryset = Transition.objects.all()
    serializer_class = TransitionSerializer
    prefetch_related = ['actions']


class TransitionView(APIView):

    def dispatch(self, *args, **kwargs):
        self.transition = Transition.objects.get(
            pk=kwargs.get('transition_id')
        )
        self.obj = self.transition.model.content_type.get_object_for_this_type(
            pk=kwargs.get('obj_pk')
        )
        self.actions, self.return_attachment = collect_actions(
            self.obj, self.transition
        )
        return super().dispatch(*args, **kwargs)

    def get_fields(self):
        fields = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
                field_class, field_attr = FIELD_MAP.get(
                    options['field'].__class__, None
                )
                attrs = {
                    name: getattr(
                        options['field'], name, None
                    ) for name in field_attr
                }
                fields[name] = field_class(**attrs)
        return fields

    def get_serializer_class(self):
        class_name = 'TransitionSerializer{}'.format(
            self.obj.__class__.__name__
        )
        class_attrs = self.get_fields()
        serializer_class = type(
            class_name, (serializers.Serializer,), class_attrs
        )

        return serializer_class

    def get_serializer(self, only_class=False):
        return self.get_serializer_class()()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        result = {'status': False}
        if serializer.is_valid():
            transition_result = run_transition(
                [self.obj],
                self.transition,
                self.transition.model.field_name,
                serializer.data,
                request=request
            )
            if self.transition.is_async:
                result['job_ids'] = transition_result
                result['status'] = True
            else:
                result['status'] = transition_result[0]
        else:
            result['errors'] = serializer.errors

        return Response(result)
