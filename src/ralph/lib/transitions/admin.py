# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.admin import TabularInline

from ralph.admin import RalphAdmin, register
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
        params = self.model._meta.app_label, self.model._meta.model_name
        url = '{}_{}_transition'.format(*params)
        if with_namespace:
            url = 'admin:' + url
        return url

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
