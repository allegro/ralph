# -*- coding: utf-8 -*-
import os
from copy import copy

from django import forms
from django.conf import settings
from django.contrib.admin.templatetags.admin_static import static
from django.db import models
from django.views.generic import TemplateView

from import_export.admin import ImportExportModelAdmin
from reversion import VersionAdmin

from ralph.admin import widgets


FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
    models.DateTimeField: {'widget': widgets.ReadOnlyWidget},
}


def get_common_media():
    """
    Shared by across extra views and admin class
    """
    js = map(lambda x: os.path.join(*x), [
        ('vendor', 'js', 'jquery.js'),
        ('vendor', 'js', 'foundation.min.js'),
        ('vendor', 'js', 'modernizr.js'),
    ])
    return forms.Media(
        js=[static('%s' % url) for url in js],
    )


class RalphAdminMixin(object):

    """Ralph admin mixin."""

    list_views = None
    change_views = None
    change_list_template = 'admin/change_list.html'
    change_form_template = 'admin/change_form.html'

    def __init__(self, *args, **kwargs):
        self.list_views = copy(self.list_views) or []
        if kwargs.get('change_views'):
            self.change_views = copy(kwargs.pop('change_views', []))
        else:
            self.change_views = copy(self.change_views) or []
        super().__init__(*args, **kwargs)

    def get_changelist(self, request, **kwargs):
        from ralph.admin.views.main import RalphChangeList
        return RalphChangeList

    def changelist_view(self, request, extra_context=None):
        """Override change list from django."""
        if extra_context is None:
            extra_context = {}
        extra_context['app_label'] = self.model._meta.app_label
        extra_context['header_obj_name'] = self.model._meta.verbose_name_plural
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
        extra_context['header_obj_name'] = self.model._meta.verbose_name
        return super(RalphAdminMixin, self).changeform_view(
            request, object_id, form_url, extra_context
        )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('user_permissions', 'permissions'):
            kwargs['widget'] = widgets.PermissionsSelectWidget()
        return db_field.formfield(**kwargs)


class RalphAdmin(ImportExportModelAdmin, RalphAdminMixin, VersionAdmin):
    def __init__(self, *args, **kwargs):
        super(RalphAdmin, self).__init__(*args, **kwargs)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_DEFAULTS)

    @property
    def media(self):
        return super().media + get_common_media()


class RalphTemplateView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(RalphTemplateView, self).get_context_data(
            **kwargs
        )
        context['site_header'] = settings.ADMIN_SITE_HEADER
        context['media'] = get_common_media()
        return context
