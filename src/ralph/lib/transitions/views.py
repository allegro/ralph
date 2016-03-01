from copy import deepcopy

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.lib.transitions.exceptions import TransitionNotAllowedError
from ralph.lib.transitions.models import (
    _check_instances_for_transition,
    run_field_transition,
    Transition
)


class TransitionViewMixin(object):
    template_name = 'transitions/run_transition.html'

    def _objects_are_valid(self):
        try:
            _check_instances_for_transition(self.objects, self.transition)
        except TransitionNotAllowedError as e:
            return False, e
        return True, None

    def collect_actions(self, transition):
        names = transition.actions.values_list('name', flat=True).all()
        actions = [getattr(self.obj, name) for name in names]
        return_attachment = [
            getattr(action, 'return_attachment', False)
            for action in actions
        ]
        return actions, any(return_attachment)

    @property
    def form_fields_from_actions(self):
        fields = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
                options = deepcopy(options)
                condition = options.get('condition', lambda x, y: True)
                if not condition(self.obj, self.actions):
                    continue
                autocomplete_model = options.get('autocomplete_model', False)
                model = self.obj
                if autocomplete_model:
                    model = get_model(autocomplete_model)

                if options.get('autocomplete_field', False):
                    field = model._meta.get_field(
                        options['autocomplete_field']
                    )
                    options['field'].widget = AutocompleteWidget(
                        field=field,
                        admin_site=ralph_site,
                        request=self.request,
                        **options.get('widget_options', {})
                    )
                else:
                    options['field'].widget.request = self.request

                default_value = options.get(
                    'default_value', lambda x, y: False
                )
                initial = default_value(self.actions, self.objects)
                if initial:
                    options['field'].initial = initial
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
        self.actions, self.return_attachment = self.collect_actions(self.transition)  # noqa
        if not len(self.form_fields_from_actions):
            return self.run_and_redirect(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context = self.get_context_data()
        return self.render_to_response(context)

    def form_valid(self, form=None):
        status, attachment = run_field_transition(
            instances=self.objects,
            transition_obj_or_name=self.transition,
            field=self.transition.model.field_name,
            data=form.cleaned_data if form else {},
            request=self.request
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

        if attachment:
            url = reverse(
                'serve_attachment',
                args=(attachment.id, attachment.original_filename)
            )
            self.request.session['attachment_to_download'] = url
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
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        raise NotImplementedError()


class RunBulkTransitionView(TransitionViewMixin, RalphTemplateView):

    def dispatch(
        self, request, transition_pk, model, *args, **kwargs
    ):
        self.model = model
        self.transition = get_object_or_404(Transition, pk=transition_pk)
        ids = [int(i) for i in self.request.GET.getlist('select')]
        self.objects = list(self.model.objects.filter(id__in=ids))
        self.obj = self.objects[0]
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        transition_back_url = self.request.GET.get('back_url', None)
        if not transition_back_url:
            info = self.model._meta.app_label, self.model._meta.model_name
            return reverse('admin:{}_{}_changelist'.format(*info))

        return transition_back_url


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
        return self.objects[0].get_absolute_url()
