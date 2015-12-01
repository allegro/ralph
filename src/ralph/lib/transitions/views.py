from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.helpers import get_model_view_url_name
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

    def get_form_fields_from_actions(self):
        fields = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
                condition = options.get('condition', lambda x: True)
                if not condition(self.obj):
                    continue
                if options.get('autocomplete_field', False):
                    rel = self.obj._meta.get_field(
                        options['autocomplete_field']
                    ).rel
                    options['field'].widget = AutocompleteWidget(
                        rel=rel,
                        admin_site=ralph_site,
                        request=self.request,
                    )
                else:
                    options['field'].widget.request = self.request
                field_key = '{}__{}'.format(action.__name__, name)
                fields[field_key] = options['field']
        return fields

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
        fields_dict = self.get_form_fields_from_actions()
        ParamsForm = type('ParamsForm', (forms.Form,), fields_dict)  # noqa
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        return ParamsForm(**form_kwargs)

    def form_invalid(self, form):
        context = self.get_context_data()
        return self.render_to_response(context)

    def form_valid(self, form):
        status, attachment = run_field_transition(
            instances=self.objects,
            transition_obj_or_name=self.transition,
            field=self.transition.model.field_name,
            data=form.cleaned_data,
            request=self.request
        )
        if status:
            messages.success(
                self.request, _('Transitions performed successfully')
            )
        if attachment:
            url = reverse(
                get_model_view_url_name(self.model, 'attachment'),
                args=(attachment.id, attachment.original_filename)
            )
            self.request.session['attachment_to_download'] = url
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        is_valid, error = self._objects_are_valid()
        if not is_valid:
            messages.info(
                self.request, _('Some assets are not valid')
            )
            additional_error_message = '<ul>'
            for obj, msgs in error.errors.items():
                additional_error_message += '<li>'
                additional_error_message += '<a href="{}">{}</a> - {}'.format(
                    obj.get_absolute_url(), obj, ','.join(msgs)
                )
                additional_error_message += '</li>'
            additional_error_message += '</ul>'
            messages.error(self.request, mark_safe(
                '{}<br>{}'.format(error.message, additional_error_message)
            ))
            return HttpResponseRedirect('..')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
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
        self.objects = self.model.objects.filter(id__in=ids)
        self.obj = self.objects[0]
        self.actions, self.return_attachment = self.collect_actions(self.transition)  # noqa,
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse('admin:{}_{}_changelist'.format(*info))


class RunTransitionView(TransitionViewMixin, RalphTemplateView):

    def dispatch(
        self, request, object_pk, transition_pk, model, *args, **kwargs
    ):
        self.model = model
        self.transition = get_object_or_404(Transition, pk=transition_pk)
        self.obj = get_object_or_404(model, pk=object_pk)
        self.objects = [self.obj]
        self.actions, self.return_attachment = self.collect_actions(self.transition)  # noqa
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.obj.get_absolute_url()
