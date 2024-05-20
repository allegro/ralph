# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from ralph.api import RalphReadOnlyAPIViewSet
from ralph.api.fields import ModelMultipleChoiceField
from ralph.lib.mixins.api import ChoiceFieldWithOtherOptionField
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption
from ralph.lib.transitions.api.serializers import (
    TransitionActionSerializer,
    TransitionJobSerializer,
    TransitionModelSerializer,
    TransitionSerializer,
    TransitionsHistorySerializer
)
from ralph.lib.transitions.exceptions import TransitionNotAllowedError
from ralph.lib.transitions.models import (
    _check_instances_for_transition,
    _transition_data_validation,
    Action,
    run_transition,
    Transition,
    TransitionJob,
    TransitionModel,
    TransitionsHistory
)
from ralph.lib.transitions.views import collect_actions, NonAtomicView

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
    forms.ModelChoiceField: (serializers.PrimaryKeyRelatedField, [
        'initial', 'required', 'queryset'
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


class TransitionsHistoryViewSet(RalphReadOnlyAPIViewSet):
    queryset = TransitionsHistory.objects.all()
    serializer_class = TransitionsHistorySerializer
    filter_fields = [
        'created', 'modified', 'transition_name',
        'source', 'target', 'object_id'
    ]


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
    select_related = ['model', 'model__content_type']


class AvailableTransitionViewSet(TransitionViewSet):
    """
    Available transitions for object.

    Example:
        GET: /api/<app_label>/<model>/<object_pk>/transitions
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            model__content_type__model=self.kwargs['model'],
            model__content_type__app_label=self.kwargs['app_label']
        )
        return queryset


class TransitionViewMixin(NonAtomicView, APIView):

    def initial(self, request, *args, **kwargs):
        self.obj = self.transition.model.content_type.get_object_for_this_type(
            pk=kwargs['obj_pk']
        )
        self.objects = [self.obj]
        self.actions, self.return_attachment = collect_actions(
            self.obj, self.transition
        )
        super().initial(request, *args, **kwargs)

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

    def _run_additional_validation(self, data):
        """
        Run additional data validation on API data and transition instances.

        Raise ValidationError (DRF) if any error occurs.
        """
        errors = _transition_data_validation(
            self.objects, self.transition, data
        )
        if errors:
            api_errors = {}
            for action_name, action_errors in errors.items():
                for field_name, field_errors in action_errors.items():
                    api_errors[field_name] = [
                        exc.message for exc in field_errors
                    ]
            raise DRFValidationError(api_errors)

    def _check_instances(self):
        try:
            _check_instances_for_transition(
                instances=self.objects,
                transition=self.transition,
                requester=self.request.user,
            )
        except TransitionNotAllowedError as e:
            raise DRFValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: list(itertools.chain(
                    *e.errors.values()
                ))
            })

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._check_instances()
        self._run_additional_validation(serializer.validated_data)
        result = {}
        data = self.add_function_name_to_data(serializer.validated_data)
        transition_result = run_transition(
            instances=self.objects,
            transition_obj_or_name=self.transition,
            field=self.transition.model.field_name,
            data=data,
            requester=request.user
        )
        status_code = status.HTTP_201_CREATED
        if self.transition.is_async:
            result['job_ids'] = [
                reverse('transitionjob-detail', args=(i,))
                for i in transition_result
            ]
            status_code = status.HTTP_202_ACCEPTED
        return Response(result, status=status_code)


class TransitionView(TransitionViewMixin):
    """
    Transition API endpoint for selected model.

    Example:
        OPTIONS: /api/<app_label>/<model>/<pk>/transitions/<transition_name>
        or <transiton_id>
    """

    def initial(self, request, *args, **kwargs):
        try:
            filters = {
                'model__content_type__model': kwargs['model'],
                'model__content_type__app_label': kwargs['app_label'],
            }
            if kwargs.get('transition_pk'):
                filters['pk'] = kwargs['transition_pk']
            elif kwargs.get('transition_name'):
                filters['name'] = kwargs['transition_name']

            self.transition = Transition.objects.get(**filters)
        except ObjectDoesNotExist:
            raise NotFound('Transition not found!')
        super().initial(request, *args, **kwargs)


class TransitionByIdView(TransitionViewMixin):

    def initial(self, request, *args, **kwargs):
        try:
            self.transition = Transition.objects.get(
                pk=kwargs['transition_pk']
            )
        except ObjectDoesNotExist:
            raise NotFound('Transition not found!')
        super().initial(request, *args, **kwargs)
