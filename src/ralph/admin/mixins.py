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
from ralph.helpers import add_request_to_form
from ralph.lib.mixins.forms import RequestFormMixin
from ralph.lib.permissions.admin import PermissionsPerObjectFormMixin
from ralph.lib.permissions.views import PermissionViewMetaClass

FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
    models.DateTimeField: {'widget': widgets.ReadOnlyWidget},
}


def get_common_media():
    """
    Shared across extra views and admin class
    """
    js = map(lambda x: os.path.join(*x), [
        ('admin', 'js', 'core.js'),
        ('admin', 'js', 'jquery.js'),
        ('admin', 'js', 'jquery.init.js'),
        ('admin', 'js', 'actions.js'),
        ('admin', 'js', 'admin', 'RelatedObjectLookups.js'),
        ('vendor', 'js', 'jquery.js'),
        ('vendor', 'js', 'foundation.min.js'),
        ('vendor', 'js', 'modernizr.js'),
        ('src', 'js', 'fill-fields.js'),
        ('vendor', 'js', 'foundation-datepicker.js'),
        ('src', 'js', 'foundation-datepicker-init.js'),
    ])
    return forms.Media(
        js=[static('%s' % url) for url in js],
    )


def get_inline_media():
    js = map(lambda x: os.path.join(*x), [
        ('admin', 'js', 'inlines.js'),
        ('src', 'js', 'ralph-autocomplete.js'),
    ])
    return forms.Media(
        js=[static('%s' % url) for url in js],
    )


class RalphAutocompleteMixin(object):
    raw_id_override_parent = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_DEFAULTS)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in self.raw_id_fields:
            kw = {}
            if db_field.name in self.raw_id_override_parent:
                kw['rel_to'] = self.raw_id_override_parent[db_field.name]
            kwargs['widget'] = widgets.AutocompleteWidget(
                db_field.rel, self.admin_site, using=kwargs.get('using'),
                request=request, **kw
            )
            return db_field.formfield(**kwargs)
        else:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RalphAdminFormMixin(PermissionsPerObjectFormMixin, RequestFormMixin):
    pass


class RalphAdminForm(RalphAdminFormMixin, forms.ModelForm):
    pass


class RalphAdminChecks(admin.checks.ModelAdminChecks):
    def _check_form(self, cls, model):
        """
        Check if form subclasses RalphAdminFormMixin
        """
        result = super()._check_form(cls, model)
        if (
            hasattr(cls, 'form') and
            not issubclass(cls.form, RalphAdminFormMixin)
        ):
            result += admin.checks.must_inherit_from(
                parent='RalphAdminFormMixin',
                option='form',
                obj=cls,
                id='admin.E016'
            )
        return result


class RalphAdminMixin(RalphAutocompleteMixin):
    """Ralph admin mixin."""

    list_views = None
    change_views = None
    change_list_template = 'admin/change_list.html'
    change_form_template = 'admin/change_form.html'

    checks_class = RalphAdminChecks
    form = RalphAdminForm

    def __init__(self, *args, **kwargs):
        self.list_views = copy(self.list_views) or []
        if kwargs.get('change_views'):
            self.change_views = copy(kwargs.pop('change_views', []))
        else:
            self.change_views = copy(self.change_views) or []
        super().__init__(*args, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """
        Return form with request param passed by default.
        """
        Form = super().get_form(request, obj, **kwargs)  # noqa
        return add_request_to_form(Form, request=request)

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
        if self.get_actions(request) or self.list_filter:
            extra_context['has_filters'] = True

        extra_context['bulk_edit'] = request.GET.get(BULK_EDIT_VAR, False)
        if extra_context['bulk_edit']:
            extra_context['has_filters'] = False
        self._initialize_search_form(extra_context)
        return super(RalphAdminMixin, self).changelist_view(
            request, extra_context
        )

    def get_actions(self, request):
        """Override get actions method."""
        if request.GET.get(BULK_EDIT_VAR, False):
            # Hide checkbox on bulk edit page
            return []
        return super().get_actions(request)

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

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('user_permissions', 'permissions'):
            kwargs['widget'] = widgets.PermissionsSelectWidget()
            return db_field.formfield(**kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class RalphAdmin(
    ImportExportModelAdmin,
    AjaxAutocompleteMixin,
    RalphAdminMixin,
    VersionAdmin
):
    @property
    def media(self):
        return super().media + get_common_media()


class RalphTabularInline(
    RalphAutocompleteMixin,
    admin.TabularInline
):
    pass


class RalphStackedInline(
    RalphAutocompleteMixin,
    admin.StackedInline
):
    pass


class RalphTemplateView(TemplateView, metaclass=PermissionViewMetaClass):

    def get_context_data(self, **kwargs):
        context = super(RalphTemplateView, self).get_context_data(
            **kwargs
        )
        context['site_header'] = settings.ADMIN_SITE_HEADER
        context['media'] = get_common_media()
        # checks if user is allowed to see elements in template
        context['has_permission'] = self.request.user.is_authenticated()
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
            bulk_list = [
                field for field in self.bulk_edit_list
                if self.model.has_access_to_field(
                    field, request.user, action='change'
                )
            ]
            list_display = bulk_list.copy()
            if 'id' not in list_display:
                list_display.insert(0, 'id')
            self.list_editable = bulk_list
            return list_display
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
