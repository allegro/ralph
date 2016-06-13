# -*- coding: utf-8 -*-
from django import forms
from django.core.urlresolvers import reverse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ralph.api import RalphReadOnlyAPIViewSet
from ralph.api.fields import ModelMultipleChoiceField
from ralph.lib.mixins.api import ChoiceFieldWithOtherOptionField
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption
from ralph.lib.transitions.api.serializers import (
    TransitionActionSerializer,
    TransitionJobSerializer,
    TransitionModelSerializer,
    TransitionSerializer
)
from ralph.lib.transitions.models import (
    Action,
    run_transition,
    Transition,
    TransitionJob,
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
    forms.ModelMultipleChoiceField: (ModelMultipleChoiceField, [
        'initial', 'required', 'choices'
    ]),
    forms.ModelChoiceField: (serializers.ChoiceField, [
        'initial', 'required', 'choices'
    ]),
    forms.ChoiceField: (serializers.ChoiceField, [
        'initial', 'required', 'choices'
    ]),
    ChoiceFieldWithOtherOption: (ChoiceFieldWithOtherOptionField, [
        'initial', 'required', 'choices', 'auto_other_choice',
        'other_option_label'
    ])
}


class TransitionJobViewSet(RalphReadOnlyAPIViewSet):
    queryset = TransitionJob.objects.all()
    serializer_class = TransitionJobSerializer


class TransitionModelViewSet(RalphReadOnlyAPIViewSet):
    queryset = TransitionModel.objects.all()
    serializer_class = TransitionModelSerializer


class TransitionActionViewSet(RalphReadOnlyAPIViewSet):
    queryset = Action.objects.all()
    serializer_class = TransitionActionSerializer


class TransitionViewSet(RalphReadOnlyAPIViewSet):
    queryset = Transition.objects.all()
    serializer_class = TransitionSerializer
    prefetch_related = ['actions']


class TransitionView(APIView):

    def dispatch(self, request, transition_pk, obj_pk, *args, **kwargs):
        self.transition = Transition.objects.get(
            pk=transition_pk
        )
        self.obj = self.transition.model.content_type.get_object_for_this_type(
            pk=obj_pk
        )
        self.objects = [self.obj]
        self.actions, self.return_attachment = collect_actions(
            self.obj, self.transition
        )
        return super().dispatch(request, *args, **kwargs)

    def get_fields(self):
        fields = {}
        fields_name_map = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
                # TODO: unify this with
                # TransitionViewMixin.form_fields_from_actions
                condition = options.get('condition', lambda x, y: True)
                if not condition(self.obj, self.actions):
                    continue
                field_class, field_attr = FIELD_MAP.get(
                    options['field'].__class__, None
                )
                attrs = {
                    name: getattr(
                        options['field'], name, None
                    ) for name in field_attr
                }
                choices = options.get('choices')
                if choices:
                    if callable(choices):
                        list_of_choices = choices(self.actions, self.objects)
                    else:
                        list_of_choices = choices.copy()
                    attrs['choices'] = list_of_choices
                fields_name_map[name] = '{}__{}'.format(action.__name__, name)
                fields[name] = field_class(**attrs)
        return fields, fields_name_map

    def get_serializer_class(self):
        class_name = 'TransitionSerializer{}'.format(
            self.obj.__class__.__name__
        )
        class_attrs, _ = self.get_fields()
        serializer_class = type(
            class_name, (serializers.Serializer,), class_attrs
        )

        return serializer_class

    def get_serializer(self, only_class=False):
        return self.get_serializer_class()()

    def add_function_name_to_data(self, data):
        result = {}
        _, fields_name_map = self.get_fields()
        for k, v in data.items():
            result[fields_name_map.get(k)] = v
        return result

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = {}
        data = self.add_function_name_to_data(serializer.validated_data)
        transition_result = run_transition(
            self.objects,
            self.transition,
            self.transition.model.field_name,
            data,
            request=request
        )
        status_code = status.HTTP_201_CREATED
        if self.transition.is_async:
            result['job_ids'] = [
                reverse('transitionjob-detail', args=(i,))
                for i in transition_result
            ]
            status_code = status.HTTP_202_ACCEPTED
        return Response(result, status=status_code)
