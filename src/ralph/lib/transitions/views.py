from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.lib.transitions.models import run_field_transition, Transition


class RunTransitionView(RalphTemplateView):
    template_name = 'transitions/run_transition.html'

    def dispatch(
        self, request, object_pk, transition_pk, model, *args, **kwargs
    ):
        self.obj = get_object_or_404(model, pk=object_pk)
        self.transition = get_object_or_404(Transition, pk=transition_pk)
        self.actions = self.collect_actions(self.transition)
        return super().dispatch(request, *args, **kwargs)

    def collect_actions(self, transition):
        names = transition.actions.values_list('name', flat=True).all()
        return [getattr(self.obj, name) for name in names]

    def get_form_fields_from_actions(self):
        fields = {}
        for action in self.actions:
            action_fields = getattr(action, 'form_fields', {})
            for name, options in action_fields.items():
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

    def get_form(self):
        form_kwargs = {}
        fields_dict = self.get_form_fields_from_actions()
        ParamsForm = type('ParamsForm', (forms.Form,), fields_dict)  # noqa
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        return ParamsForm(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['transition'] = self.transition
        context['back_url'] = self.obj.get_absolute_url()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        return self.render_to_response(context)

    def form_valid(self, form):
        run_field_transition(
            instance=self.obj,
            transition=self.transition,
            field=self.transition.model.field_name,
            data=form.cleaned_data,
        )
        messages.success(self.request, _('Transitions performed successfully'))
        return HttpResponseRedirect(self.obj.get_absolute_url())
