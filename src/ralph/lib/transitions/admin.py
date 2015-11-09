# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.admin import TabularInline

from ralph.admin import RalphAdmin, register
from ralph.helpers import get_model_view_url_name
from ralph.lib.transitions.forms import TransitionForm
from ralph.lib.transitions.models import Transition, TransitionModel
from ralph.lib.transitions.views import RunTransitionView


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
    run_transition_view = RunTransitionView

    def get_transition_url_name(self, with_namespace=True):
        return get_model_view_url_name(
            self.model, 'transition', with_namespace
        )

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
                self.admin_site.admin_view(self.run_transition_view.as_view()),
                {'model': self.model},
                name=self.get_transition_url_name(False),
            ),
        ]
        return transitions_urls + urls
