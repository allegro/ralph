from copy import deepcopy
from itertools import repeat

from django import forms
from django.apps import apps
from django.contrib import messages
from django.db.transaction import atomic, non_atomic_requests
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.decorators import classonlymethod
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from ralph.admin.helpers import get_admin_url
from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.lib.permissions.views import PermissionViewMetaClass
from ralph.lib.transitions.exceptions import TransitionNotAllowedError
from ralph.lib.transitions.models import (
    _check_instances_for_transition,
    _transition_data_validation,
    run_transition,
    Transition,
    TransitionJob
)


def collect_actions(obj, transition):
    names = transition.actions.values_list('name', flat=True).all()
    actions = [getattr(obj, name) for name in names]
    return_attachment = [
        getattr(action, 'return_attachment', False)
        for action in actions
    ]
    return actions, any(return_attachment)


def build_params_url_for_redirect(ids):
    return urlencode(list(zip(repeat('select', len(ids)), ids)))


class NonAtomicView(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Don't run (async) request for transition atomically. When job is
        scheduled to worker, transaction has to be already commited, to allow
        worker to fetch Job from database.
        """
        return non_atomic_requests(super().as_view(**initkwargs))


class TransitionViewMixin(NonAtomicView, object):
    template_name = 'transitions/run_transition.html'

    def _objects_are_valid(self):
        try:
            _check_instances_for_transition(
                instances=self.objects,
                transition=self.transition,
                requester=self.request.user
            )
        except TransitionNotAllowedError as e:
            return False, e
        return True, None

    def get_template_names(self):
        template_names = super().get_template_names()
        if self.transition.template_name:
            template_names.insert(0, self.transition.template_name)
        return template_names

    @property
    def form_fields_from_actions(self):
        fields = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
                options = deepcopy(options)
                condition = options.get('condition', lambda x, y: True)
                choices = options.get('choices')
                field = options.get('field')
                autocomplete_field = options.get('autocomplete_field', False)
                if not condition(self.obj, self.actions):
                    continue
                autocomplete_model = options.get('autocomplete_model', False)
                model = self.obj
                if autocomplete_model:
                    model = apps.get_model(autocomplete_model)

                if autocomplete_field:
                    field = model._meta.get_field(autocomplete_field)
                    options['field'].widget = AutocompleteWidget(
                        field=field,
                        admin_site=ralph_site,
                        request=self.request,
                        **options.get('widget_options', {})
                    )

                if choices:
                    if callable(choices):
                        list_of_choices = choices(self.actions, self.objects)
                    else:
                        list_of_choices = choices.copy()
                    if field:
                        field.choices = list_of_choices
                    else:
                        options['field'] = forms.ChoiceField(
                            choices=list_of_choices
                        )

                default_value = options.get(
                    'default_value', lambda x, y: False
                )
                initial = default_value(self.actions, self.objects)
                if initial:
                    options['field'].initial = initial

                if not autocomplete_field:
                    options['field'].widget.request = self.request

                field_key = '{}__{}'.format(action.__name__, name)
                fields[field_key] = options['field']
        return fields

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'transition'):
            return HttpResponseBadRequest()
        if not request.user.has_perm(
            '{}.{}'.format(
                self.transition.permission_info['content_type'].app_label,
                self.transition.permission_info['codename'],
            )
        ):
            return HttpResponseForbidden()
        self.actions, self.return_attachment = collect_actions(
            self.obj, self.transition
        )
        if not len(self.form_fields_from_actions):
            return self.run_and_redirect(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        context['transition'] = self.transition
        context['back_url'] = self.get_success_url()
        context['objects'] = self.objects
        context['verbose_name'] = self.obj._meta.verbose_name
        return context

    def get_form(self):
        form_kwargs = {}
        fields_dict = self.form_fields_from_actions
        ParamsForm = type('ParamsForm', (forms.Form,), fields_dict)  # noqa
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        return ParamsForm(**form_kwargs)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form=None):
        if self.transition.is_async:
            # commited manually in Job.run
            return self._run_async_transition(form)
        else:
            with atomic():
                return self._run_synchronous_transition(form)

    def _run_async_transition(self, form):
        job_ids = run_transition(
            instances=self.objects,
            transition_obj_or_name=self.transition,
            field=self.transition.model.field_name,
            data=form.cleaned_data if form else {},
            requester=self.request.user
        )
        return HttpResponseRedirect(
            self.get_async_transitions_awaiter_url(job_ids)
        )

    def _run_synchronous_transition(self, form):
        status, attachments = run_transition(
            instances=self.objects,
            transition_obj_or_name=self.transition,
            field=self.transition.model.field_name,
            data=form.cleaned_data if form else {},
            requester=self.request.user
        )
        if status:
            messages.success(
                self.request, _('Transitions performed successfully')
            )
        else:
            messages.error(
                self.request, _((
                    'Something went wrong while displaying this transition. '
                    'To continue, reload or go to another transition.'
                ))
            )
            return self.form_invalid(form)
        if attachments:
            urls = [reverse(
                'serve_attachment',
                args=(attachment.id, attachment.original_filename)
            ) for attachment in attachments]
            self.request.session['attachments_to_download'] = urls
        return HttpResponseRedirect(self.get_success_url())

    def _is_valid(self):
        is_valid, error = self._objects_are_valid()
        if not is_valid:
            messages.info(
                self.request, _('Some assets are not valid')
            )
            additional_error_message = '<ul>'
            for obj, msgs in error.errors.items():
                additional_error_message += '<li>'
                additional_error_message += '<a href="{}">{}</a> - {}'.format(
                    obj.get_absolute_url(), obj, ','.join(map(str, msgs))
                )
                additional_error_message += '</li>'
            additional_error_message += '</ul>'
            messages.error(self.request, mark_safe(
                '{}<br>{}'.format(error.message, additional_error_message)
            ))
            return HttpResponseRedirect('..')
        return None

    def run_and_redirect(self, request, *args, **kwargs):
        return self._is_valid() or self.form_valid()

    def get(self, request, *args, **kwargs):
        return self._is_valid() or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        not_valid = self._is_valid()
        if not_valid:
            return not_valid

        form = self.get_form()
        if form.is_valid():
            # additional data validation
            form_errors = _transition_data_validation(
                self.objects, self.transition, form.cleaned_data
            )
            if form_errors:
                for action, action_errors in form_errors.items():
                    for field_name, field_errors in action_errors.items():
                        form.add_error(
                            action + '__' + field_name, field_errors
                        )
            else:
                return self.form_valid(form)
        return self.form_invalid(form)

    def get_async_transitions_awaiter_url(self, job_ids):
        return '{}?{}'.format(
            reverse('async_bulk_transitions_awaiter'),
            urlencode(MultiValueDict([('jobid', job_id) for job_id in job_ids]))
        )

    def get_success_url(self):
        raise NotImplementedError()


class RunBulkTransitionView(TransitionViewMixin, RalphTemplateView):

    def dispatch(
        self, request, transition_pk, model, *args, **kwargs
    ):
        self.model = model
        self.transition = get_object_or_404(Transition, pk=transition_pk)
        self.ids = [int(i) for i in self.request.GET.getlist('select')]
        self.objects = list(self.model.objects.filter(id__in=self.ids))
        self.obj = self.objects[0]
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        transition_success_url = self.transition.success_url
        if transition_success_url:
            transition_success_url += '?' + build_params_url_for_redirect(
                self.ids
            )
        transition_back_url = self.request.GET.get('back_url', None)
        if not transition_back_url:
            info = self.model._meta.app_label, self.model._meta.model_name
            transition_back_url = reverse(
                'admin:{}_{}_changelist'.format(*info)
            )
        return transition_success_url or transition_back_url


class RunTransitionView(TransitionViewMixin, RalphTemplateView):

    def dispatch(
        self, request, object_pk, transition_pk, model, *args, **kwargs
    ):
        self.model = model
        self.transition = get_object_or_404(Transition, pk=transition_pk)
        self.obj = get_object_or_404(model, pk=object_pk)
        self.objects = [self.obj]
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.transition.success_url or self.objects[0].get_absolute_url()

    def get_async_transitions_awaiter_url(self, job_ids):
        return get_admin_url(self.objects[0], 'current_transitions')


class AsyncBulkTransitionsAwaiterView(RalphTemplateView):
    template_name = 'transitions/async_transitions_awaiter.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        job_ids = self.request.GET.getlist('jobid')
        try:
            jobs = list(TransitionJob.objects.filter(pk__in=job_ids))
            if len(jobs) != len(job_ids):
                raise ValueError()
        except ValueError:
            raise Http404()  # ?
        else:
            context['jobs'] = jobs
            context['are_jobs_running'] = any([j.is_running for j in jobs])
            context['for_many_objects'] = True
        return context


class KillTransitionJobView(View, metaclass=PermissionViewMetaClass):

    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(TransitionJob, pk=job_id)
        job.kill()
        messages.success(request, 'Job {} killed successfully'.format(job.id))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
