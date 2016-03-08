# -*- coding: utf-8 -*-
from string import Formatter
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Region, Team
from ralph.admin import RalphAdmin, register
from ralph.admin.helpers import getattr_dunder
from ralph.admin.mixins import RalphAdminFormMixin
from ralph.admin.views.extra import RalphDetailView
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.table import Table
from ralph.lib.transitions.models import TransitionsHistory
from ralph.licences.models import Licence

# use string for whole app (app_label) or tuple (app_label, model_name) to
# exclude particular model
PERMISSIONS_EXCLUDE = [
    'admin',
    'attachment',
    'authtoken',
    'contenttypes',
    'data_importer',
    'reversion',
    'sessions',
    'sitetree',
    'taggit',
    ('assets', 'assetlasthostname'),
    ('transitions', 'action'),
    ('transitions', 'transitionshistory'),
    ('transitions', 'transitionmodel'),
]


class EditPermissionsFormMixin(object):
    def _simplify_permissions(self, queryset):
        """
        Exclude some permissions from widget.

        Permissions to exclude are defined in PERMISSIONS_EXCLUDE.
        """
        queryset = queryset.exclude(content_type__app_label__in=[
            ct for ct in PERMISSIONS_EXCLUDE if not isinstance(
                ct, (tuple, list)
            )
        ])
        for value in PERMISSIONS_EXCLUDE:
            if isinstance(value, (tuple, list)):
                app_label, model_name = value
                queryset = queryset.exclude(
                    content_type__app_label=app_label,
                    content_type__model=model_name
                )
        queryset = queryset.select_related('content_type').order_by(
            'content_type__model'
        )
        return queryset


class RalphUserChangeForm(
    EditPermissionsFormMixin, RalphAdminFormMixin, UserAdmin.form
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get('user_permissions', None)
        if field:
            self._simplify_permissions(field.queryset)


class AssetList(Table):

    def url(self, item):
        return '<a href="{}">{}</a>'.format(
            reverse(
                'admin:back_office_backofficeasset_change',
                args=(item.id,)
            ),
            _('go to asset')
        )
    url.title = _('Link')

    def buyout_date(self, item):
        if item.model.category.show_buyout_date:
            return item.buyout_date
        return '&mdash;'
    buyout_date.title = _('Buyout date')

    def user_licence(self, item):
        licences = item.licences.select_related('licence')
        if licences:
            result = [
                '<a href="{}">{}</a><br />'.format(
                    reverse(
                        'admin:licences_licence_change',
                        args=(licence.licence.pk,)
                    ),
                    licence.licence
                ) for licence in licences
            ]
            return [''.join(result)]
        else:
            return []

    def report_failure(self, item):
        item_dict = model_to_dict(item)
        url = settings.MY_EQUIPMENT_REPORT_FAILURE_URL
        if url:
            placeholders = [
                k[1] for k in Formatter().parse(url) if k[1] is not None
            ]
            item_dict.update({
                k: getattr_dunder(item, k) for k in placeholders
            })
            if self.request and 'username' not in item_dict:
                item_dict['username'] = self.request.user.username

            def escape_param(p):
                """
                Escape URL param and replace quotation by unicode inches sign
                """
                return quote(str(p).replace('"', '\u2033'))
            return '<a href="{}" target="_blank">{}</a><br />'.format(
                url.format(
                    **{k: escape_param(v) for (k, v) in item_dict.items()}
                ),
                _('Report failure')
            )
        return ''
    report_failure.title = ''


class AssignedLicenceList(Table):

    def url(self, item):
        return '<a href="{}">{}</a>'.format(
            reverse(
                'admin:licences_licence_change',
                args=(item.id,)
            ),
            _('go to licence')
        )
    url.title = _('Link')


class UserInfoMixin(object):
    user = None

    def get_user(self):
        if not self.user:
            raise NotImplementedError('Please specify user.')
        return self.user

    def get_asset_queryset(self):
        return BackOfficeAsset.objects.filter(
            Q(user=self.get_user()) | Q(owner=self.get_user())
        ).select_related('model', 'model__category', 'model__manufacturer')

    def get_licence_queryset(self):
        return Licence.objects.filter(
            users=self.get_user()
        ).select_related('software')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: check permission to field or model
        context['asset_list'] = AssetList(
            self.get_asset_queryset(),
            [
                'id', 'model__category__name', 'model__manufacturer__name',
                'model__name', 'sn', 'barcode', 'remarks', 'status',
                'buyout_date', 'url'
            ],
            ['user_licence']
        )
        context['licence_list'] = AssignedLicenceList(
            self.get_licence_queryset(),
            ['id', 'software__name', 'niw', 'url']
        )
        return context


class UserInfoView(UserInfoMixin, RalphDetailView):
    icon = 'user'
    name = 'user_additional_info'
    label = _('Additional info')
    url_name = 'user_additional_info'

    def get_user(self):
        return self.object


class UserTransitionHistoryView(RalphDetailView):
    icon = 'history'
    name = 'user_transition_history'
    label = _('Transition history')
    url_name = 'user_transition_history'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transitions_history'] = TransitionsHistory.objects.filter(
            Q(kwargs__icontains=self.object.username) |
            Q(kwargs__icontains=self.object.get_full_name())
        ).distinct()
        context['transition_history_in_fieldset'] = False
        return context


@register(RalphUser)
class RalphUserAdmin(UserAdmin, RalphAdmin):

    form = RalphUserChangeForm
    change_views = [
        UserInfoView,
        UserTransitionHistoryView
    ]
    readonly_fields = ('api_token_key',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'api_token_key')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions', 'regions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Profile'), {
            'fields': (
                'gender', 'country', 'city'
            )
        }),
        (_('Job info'), {
            'fields': (
                'company', 'profit_center', 'cost_center', 'department',
                'manager', 'location', 'segment', 'team',
            )
        })
    )

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related(
            'auth_token'
        )


@register(Group)
class RalphGroupAdmin(EditPermissionsFormMixin, GroupAdmin, RalphAdmin):
    readonly_fields = ['ldap_mapping', 'users_list']
    fieldsets = (
        (None, {'fields': ['name', 'ldap_mapping', 'permissions']}),
        ('Users', {'fields': ['users_list']}),
    )

    @cached_property
    def _ldap_groups(self):
        groups = {v: k for (k, v) in getattr(
            settings, 'AUTH_LDAP_GROUP_MAPPING', {}
        ).items()}
        groups.update({v: k for (k, v) in getattr(
            settings, 'AUTH_LDAP_NESTED_GROUPS', {}
        ).items()})
        return groups

    def ldap_mapping(self, obj):
        return self._ldap_groups.get(obj.name, '-')
    ldap_mapping.short_description = _('LDAP mapping')

    def users_list(self, obj):
        users = []
        for u in obj.user_set.order_by('username'):
            users.append('<a href="{}">{}</a>'.format(
                reverse("admin:accounts_ralphuser_change", args=(u.id,)),
                str(u)
            ))
        return '<br>'.join(users)
    users_list.short_description = _('Users list')
    users_list.allow_tags = True

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.rel.to.objects)
            if qs:
                qs = self._simplify_permissions(qs)
            kwargs['queryset'] = qs
        return super().formfield_for_manytomany(
            db_field, request=request, **kwargs
        )


@register(Region)
class RegionAdmin(RalphAdmin):
    search_fields = ['name']


@register(Team)
class TeamAdmin(RalphAdmin):
    search_fields = ['name']
