# -*- coding: utf-8 -*-
import os
import urllib
from copy import copy

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from import_export.admin import ImportExportModelAdmin
from reversion import VersionAdmin

from ralph.admin import widgets
from ralph.admin.autocomplete import AjaxAutocompleteMixin
from ralph.admin.helpers import get_field_by_relation_path
from ralph.admin.views.main import BULK_EDIT_VAR, BULK_EDIT_VAR_IDS

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
        ('admin', 'js', 'inlines.js'),
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

    def _initialize_search_form(self, extra_context):
        search_fields = []
        for field_name in self.search_fields:
            field = get_field_by_relation_path(self.model, field_name)
            search_fields.append(field.verbose_name)
        extra_context['search_fields'] = search_fields
        extra_context['search_url'] = urlresolvers.reverse(
            'admin:{app_label}_{model_name}_changelist'.format(
                app_label=self.model._meta.app_label,
                model_name=self.model._meta.model_name,
            )
        )

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
        self._initialize_search_form(extra_context)
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
        self._initialize_search_form(extra_context)
        return super(RalphAdminMixin, self).changeform_view(
            request, object_id, form_url, extra_context
        )

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.AutocompleteWidget(
                db_field.rel, self.admin_site, using=kwargs.get('using'),
                request=request,
            )
            return db_field.formfield(**kwargs)
        else:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('user_permissions', 'permissions'):
            kwargs['widget'] = widgets.PermissionsSelectWidget()
        return db_field.formfield(**kwargs)


class RalphAdmin(
    ImportExportModelAdmin,
    AjaxAutocompleteMixin,
    RalphAdminMixin,
    VersionAdmin
):
    def __init__(self, *args, **kwargs):
        super(RalphAdmin, self).__init__(*args, **kwargs)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_DEFAULTS)

    @property
    def media(self):
        return super().media + get_common_media()

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)  # noqa
        Form._request = request
        return Form


class RalphTemplateView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(RalphTemplateView, self).get_context_data(
            **kwargs
        )
        context['site_header'] = settings.ADMIN_SITE_HEADER
        context['media'] = get_common_media()
        return context


class BulkEditChangeListMixin(object):

    def get_queryset(self, request):
        """Override django admin get queryset method."""
        qs = super().get_queryset(request)
        id_list = request.GET.getlist(BULK_EDIT_VAR_IDS, [])
        if id_list:
            qs = qs.filter(pk__in=id_list)
        return qs

    def get_list_display(self, request):
        """
        Override django admin get list display method.
        Set new values for fields list_editable and list_display.
        """
        if request.GET.get(BULK_EDIT_VAR):
            bulk_list = self.bulk_edit_list
            list_display = bulk_list.copy()
            if 'id' not in list_display:
                list_display.insert(0, 'id')
            self.list_editable = bulk_list
            self.list_display = list_display
        else:
            self.list_editable = []
        return self.list_display

    def bulk_edit_action(self, request, queryset):
        """
        Custom bulk edit action.
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        url = reverse('admin:{}'.format(request.resolver_match.url_name))
        id_list = [(BULK_EDIT_VAR_IDS, i) for i in selected]
        return HttpResponseRedirect(
            '{}?{}=1&{}'.format(
                url,
                BULK_EDIT_VAR,
                urllib.parse.urlencode(id_list),
            )
        )

    bulk_edit_action.short_description = 'Bulk edit'
