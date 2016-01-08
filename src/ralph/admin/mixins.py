# -*- coding: utf-8 -*-
import os
import urllib
from copy import copy

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.auth import get_permission_codename
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTAdminForm, MPTTModelAdmin
from reversion import VersionAdmin

from ralph.admin import widgets
from ralph.admin.autocomplete import AjaxAutocompleteMixin
from ralph.admin.helpers import get_field_by_relation_path
from ralph.admin.views.main import BULK_EDIT_VAR, BULK_EDIT_VAR_IDS
from ralph.helpers import add_request_to_form
from ralph.lib.mixins.forms import RequestFormMixin
from ralph.lib.permissions.admin import PermissionsPerObjectFormMixin
from ralph.lib.permissions.models import PermByFieldMixin
from ralph.lib.permissions.views import PermissionViewMetaClass

FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
    models.DateTimeField: {'widget': widgets.ReadOnlyWidget},
}


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
                field=db_field, admin_site=self.admin_site,
                using=kwargs.get('using'), request=request, **kw
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


class RalphMPTTAdminForm(RalphAdminFormMixin, MPTTAdminForm):
    pass


class RalphAdminMixin(RalphAutocompleteMixin):
    """Ralph admin mixin."""

    list_views = None
    change_views = None
    change_list_template = 'admin/change_list.html'
    change_form_template = 'admin/change_form.html'
    checks_class = RalphAdminChecks
    form = RalphAdminForm
    # List of fields that are to be excluded from fillable on bulk edit
    bulk_edit_no_fillable = []
    _queryset_manager = None

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

    def has_view_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('view', opts)
        return request.user.has_perm('%s.%s' % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        if obj:
            return super().has_change_permission(request, obj)
        else:
            return self.has_view_permission(request, obj)

    def get_changelist(self, request, **kwargs):
        from ralph.admin.views.main import RalphChangeList
        return RalphChangeList

    def get_list_display_links(self, request, list_display):
        if super().has_change_permission(request):
            return super().get_list_display_links(request, list_display)
        else:
            return None

    def _initialize_search_form(self, extra_context):
        search_fields = []
        for field_name in self.search_fields:
            field = get_field_by_relation_path(self.model, field_name)
            search_fields.append(field.verbose_name)
        extra_context['search_fields'] = search_fields
        extra_context['search_url'] = reverse(
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
            bulk_back_url = request.session.get('bulk_back_url')
            if not bulk_back_url:
                bulk_back_url = request.META.get('HTTP_REFERER')
                request.session['bulk_back_url'] = bulk_back_url
            extra_context['bulk_back_url'] = bulk_back_url
            extra_context['has_filters'] = False
        else:
            request.session['bulk_back_url'] = None

        self._initialize_search_form(extra_context)
        return super(RalphAdminMixin, self).changelist_view(
            request, extra_context
        )

    def get_actions(self, request):
        """Override get actions method."""
        if request.GET.get(BULK_EDIT_VAR, False):
            # Hide checkbox on bulk edit page
            return []
        actions = super().get_actions(request)
        if (
            not self.has_delete_permission(request) and
            'delete_selected' in actions
        ):
            del actions['delete_selected']
        return actions

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
        extra_context['admin_view'] = self
        return super(RalphAdminMixin, self).changeform_view(
            request, object_id, form_url, extra_context
        )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('user_permissions', 'permissions'):
            kwargs['widget'] = widgets.PermissionsSelectWidget()
            return db_field.formfield(**kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_changelist_form(self, request, **kwargs):
        """
        Returns a FormSet class for use on the changelist page if list_editable
        is used.
        """
        if self.bulk_edit_no_fillable:
            widgets = {}
            for field_name in self.bulk_edit_no_fillable:
                field = self.model._meta.get_field(field_name)
                widget = field.formfield().widget
                # Added vTextField CSS class to widget,
                # because Django admin form has it default
                widget.attrs['class'] = 'vTextField no-fillable'
                widgets[field_name] = widget
            if widgets:
                kwargs['widgets'] = widgets
        return super().get_changelist_form(request, **kwargs)

    def _add_recovery_to_extra_context(self, extra_context):
        extra_context = extra_context or {}
        extra_context['in_recovery_mode'] = True
        return extra_context

    def revision_view(
        self, request, object_id, version_id, extra_context=None
    ):
        extra_context = self._add_recovery_to_extra_context(extra_context)
        return super().revision_view(
            request, object_id, version_id, extra_context
        )

    def get_queryset(self, *args, **kwargs):
        if self._queryset_manager:
            return getattr(self.model, self._queryset_manager).all()
        return super().get_queryset(*args, **kwargs)


class RalphAdmin(
    ImportExportModelAdmin,
    AjaxAutocompleteMixin,
    RalphAdminMixin,
    VersionAdmin
):
    @property
    def media(self):
        return forms.Media()


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


class RalphBaseTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_header'] = settings.ADMIN_SITE_HEADER
        context['site_title'] = settings.ADMIN_SITE_TITLE
        # checks if user is allowed to see elements in template
        context['has_permission'] = self.request.user.is_authenticated()
        return context


class RalphTemplateView(
    RalphBaseTemplateView, metaclass=PermissionViewMetaClass
):
    pass


class RalphMPTTAdmin(MPTTModelAdmin, RalphAdmin):
    form = RalphMPTTAdminForm


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
        self.list_editable = []
        if request.GET.get(BULK_EDIT_VAR):
            # separate read-only and editable fields
            bulk_list_display = self.bulk_edit_list
            bulk_list_edit = self.bulk_edit_list
            if isinstance(self.model, PermByFieldMixin):
                bulk_list_display = [
                    field for field in self.bulk_edit_list
                    if self.model.has_access_to_field(
                        field, request.user, action='view'
                    )
                ]
                bulk_list_edit = [
                    field for field in bulk_list_display
                    if self.model.has_access_to_field(
                        field, request.user, action='change'
                    )
                ]
            # overwrite displayed fields in bulk-edit mode
            list_display = bulk_list_display.copy()
            if 'id' not in list_display:
                list_display.insert(0, 'id')
            # list editable is subset of list display in this case
            self.list_editable = bulk_list_edit
            return list_display
        return super().get_list_display(request)

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
