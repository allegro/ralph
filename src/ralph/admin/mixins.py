# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
from copy import copy

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.views.generic import TemplateView
from reversion import VersionAdmin

from ralph.admin import widgets
from ralph.admin.signals import admin_get_list_views, admin_get_change_views


FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
}

ExtraViewItem = namedtuple('ExtraViewItem', ['label', 'name', 'url', 'icon'])


class RalphAdminMixin(object):

    """Ralph admin mixin."""

    list_views = None
    change_views = None
    change_list_template = 'ralph_admin/change_list.html'
    change_form_template = 'ralph_admin/change_form.html'

    def _get_views(self, views, signal):
        views = copy(views) or []
        signal.send(sender=self, model=self.model, views=views)
        return views

    def get_view_item(self, view, action, *args):
        info = self.model._meta.app_label, self.model._meta.model_name, action
        return ExtraViewItem(
            label=view.label,
            name=view.name,
            icon=view.icon,
            url='{}{}/'.format(
                reverse('admin:{}_{}_{}'.format(*info), args=args),
                view.url_name
            ),
        )

    def get_list_views(self):
        return self._get_views(self.list_views, admin_get_list_views)

    def get_change_views(self):
        return self._get_views(self.change_views, admin_get_change_views)

    def changelist_view(self, request, extra_context=None):
        """Override change list from django."""
        if extra_context is None:
            extra_context = {}
        extra_context['app_label'] = self.model._meta.app_label
        views = []
        for view in self.get_list_views():
            views.append(self.get_view_item(view, 'changelist'))
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
            for view in self.get_change_views():
                views.append(self.get_view_item(view, 'change', object_id))
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
