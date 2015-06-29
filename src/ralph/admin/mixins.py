# -*- coding: utf-8 -*-
from copy import copy

from django.conf import settings
from django.db import models
from django.views.generic import TemplateView
from reversion import VersionAdmin

from ralph.admin import widgets


FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
}


class RalphAdminMixin(object):

    """Ralph admin mixin."""

    list_views = None
    change_views = None
    change_list_template = 'ralph_admin/change_list.html'
    change_form_template = 'ralph_admin/change_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_views = copy(self.list_views) or []
        self.change_views = copy(self.change_views) or []

    def changelist_view(self, request, extra_context=None):
        """Override change list from django."""
        if extra_context is None:
            extra_context = {}
        extra_context['app_label'] = self.model._meta.app_label
        views = []
        for view in self.list_views:
            views.append(view)
        extra_context['list_views'] = views
        return super(RalphAdminMixin, self).changelist_view(
            request, extra_context
        )

    def changeform_view(
        self, request, object_id=None, form_url='', extra_context=None
    ):
        if extra_context is None:
            extra_context = {}
        views = []
        if object_id:
            for view in self.change_views:
                views.append(view)
            extra_context['change_views'] = views
        return super(RalphAdminMixin, self).changeform_view(
            request, object_id, form_url, extra_context
        )


class RalphAdmin(RalphAdminMixin, VersionAdmin):
    def __init__(self, *args, **kwargs):
        super(RalphAdmin, self).__init__(*args, **kwargs)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_DEFAULTS)


class RalphTemplateView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(RalphTemplateView, self).get_context_data(
            **kwargs
        )
        context['site_header'] = settings.ADMIN_SITE_HEADER
        return context
