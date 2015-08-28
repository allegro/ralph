# -*- coding: utf-8 -*-
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Region
from ralph.admin import RalphAdmin, register
from ralph.admin.mixins import RalphAdminFormMixin
from ralph.admin.views.extra import RalphDetailView
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.table import Table
from ralph.licences.models import BaseObjectLicence, Licence


class RalphUserChangeForm(RalphAdminFormMixin, UserAdmin.form):
    pass


class AssetList(Table):

    def url(self, item):
        return '<a href="{}">{}</a>'.format(
            reverse(
                'admin:back_office_backofficeasset_change',
                args=(item['id'],)
            ),
            _('go to asset')
        )
    url.title = _('Link')

    def user_licence(self, item):
        licences = BaseObjectLicence.objects.filter(
            base_object=item['id']
        ).select_related('licence')
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


class AssignedLicenceList(Table):

    def url(self, item):
        return '<a href="{}">{}</a>'.format(
            reverse(
                'admin:licences_licence_change',
                args=(item['id'],)
            ),
            _('go to licence')
        )
    url.title = _('Link')


class UserInfoView(RalphDetailView):
    icon = 'user'
    name = 'user_additional_info'
    label = _('Additional info')
    url_name = 'user_additional_info'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_list_queryset = BackOfficeAsset.objects.filter(
            user=self.object
        ).select_related('model', 'model__category', 'model__manufacturer')
        licence_list_queryset = Licence.objects.filter(
            users=self.object
        ).select_related('software_category')

        context['asset_list'] = AssetList(
            asset_list_queryset,
            [
                'id', 'model__category__name', 'model__manufacturer__name',
                'model__name', 'sn', 'barcode', 'remarks', 'status', 'url'
            ],
            ['user_licence']
        )
        context['licence_list'] = AssignedLicenceList(
            licence_list_queryset,
            ['id', 'software_category__name', 'niw', 'url']
        )
        return context


@register(RalphUser)
class RalphUserAdmin(UserAdmin, RalphAdmin):

    form = RalphUserChangeForm
    change_views = [
        UserInfoView
    ]
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Profile'), {
            'fields': (
                'gender', 'country', 'city', 'regions'
            )
        }),
        (_('Job info'), {
            'fields': (
                'company', 'profit_center', 'cost_center', 'department',
                'manager', 'location', 'segment'
            )
        })
    )


@register(Group)
class RalphGroupAdmin(GroupAdmin, RalphAdmin):
    pass


@register(Region)
class RegionAdmin(RalphAdmin):
    search_fields = ['name']
