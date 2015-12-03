# -*- coding: utf-8 -*-
from itertools import repeat

from django.conf.urls import url
from django.contrib.admin import TabularInline
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.functional import curry
from django.utils.http import urlencode

from ralph.admin import RalphAdmin, register
from ralph.helpers import get_model_view_url_name
from ralph.lib.transitions.forms import TransitionForm
from ralph.lib.transitions.models import Transition, TransitionModel
from ralph.lib.transitions.views import RunBulkTransitionView, RunTransitionView


class TransitionInline(TabularInline):
    model = Transition
    form = TransitionForm
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        class form_with_parent_instance(self.form):  # noqa
            _transition_model_instance = obj
        self.form = form_with_parent_instance
        return super().get_formset(request, obj, **kwargs)


@register(TransitionModel)
class TransitionModelAdmin(RalphAdmin):
    list_display = ['content_type', 'field_name']
    readonly_fields = ['content_type', 'field_name']
    inlines = [TransitionInline]

    def has_add_permission(self, request):
        return False


class TransitionAdminMixin(object):
    transition_view = RunTransitionView
    bulk_transition_view = RunBulkTransitionView

    def get_transition_url_name(self, with_namespace=True):
        return get_model_view_url_name(
            self.model, 'transition', with_namespace
        )

    def get_transition_bulk_url_name(self, with_namespace=True):
        return self.get_transition_url_name(with_namespace) + '_bulk'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context.update({
            'transition_url_name': self.get_transition_url_name()
        })
        return super().change_view(
            request, object_id, form_url, extra_context
        )

    def get_urls(self):
        urls = super().get_urls()
        transitions_urls = [
            url(
                r'^(?P<object_pk>.+)/transition/(?P<transition_pk>\d+)$',
                self.admin_site.admin_view(self.transition_view.as_view()),
                {'model': self.model},
                name=self.get_transition_url_name(False),
            ),
            url(
                r'^transition/(?P<transition_pk>\d+)$',
                self.admin_site.admin_view(self.bulk_transition_view.as_view()),
                {'model': self.model},
                name=self.get_transition_bulk_url_name(False),
            ),
        ]
        return transitions_urls + urls

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not actions:
            return actions
        for transition in Transition.transitions_for_model(self.model):
            name = transition.name
            actions[name] = self.get_admin_action_from_transition(transition)
        return actions

    def get_admin_action_from_transition(self, transition):
        name = transition.name

        def transition_action_redirect(cls, request, queryset, transition):
            base_url = reverse(
                self.get_transition_bulk_url_name(),
                args=(transition.pk,)
            )
            ids = queryset.values_list('id', flat=True)
            select_url = urlencode(zip(repeat('select', len(ids)), ids))
            return HttpResponseRedirect(
                base_url + '?' + select_url
            )

        return (
            curry(transition_action_redirect, transition=transition),
            name,
            '{} transition'.format(name.capitalize()),
        )
