# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.admin import AssetList, AssignedLicenceList, UserInfoMixin
from ralph.admin.mixins import RalphBaseTemplateView, RalphTemplateView
from ralph.licences.models import BaseObjectLicence


class UserProfileView(RalphTemplateView):
    template_name = 'ralphuser/user_profile.html'


class MyEquipmentAssetList(AssetList):
    def user_licence(self, item):
        licences = BaseObjectLicence.objects.filter(
            base_object=item.id
        ).select_related('licence', 'licence__software')
        if licences:
            result = [
                '&emsp; <i class="fa fa-chevron-right"></i> {} ({})'.format(
                    bo_licence.licence.software.name,
                    bo_licence.licence.niw,
                ) for bo_licence in licences
            ]
            return ['<br />'.join(result)]
        else:
            return []


class CurrentUserInfoView(UserInfoMixin, RalphBaseTemplateView):
    template_name = 'ralphuser/my_equipment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_equipment_links'] = self.get_links()
        asset_fields = [
            ('barcode', _('Barcode / Inventory Number')),
            'model__category__name', 'model__manufacturer__name',
            'model__name', ('sn', _('Serial Number')), 'invoice_date', 'status'
        ]
        if settings.MY_EQUIPMENT_SHOW_BUYOUT_DATE:
            asset_fields += ['buyout_date']

        if settings.MY_EQUIPMENT_REPORT_FAILURE_URL:
            asset_fields += ['report_failure']
        context['asset_list'] = MyEquipmentAssetList(
            self.get_asset_queryset(),
            asset_fields,
            ['user_licence'],
            request=self.request,
        )
        context['licence_list'] = AssignedLicenceList(
            self.get_licence_queryset(),
            [
                ('niw', _('Inventory Number')), 'software__name', 'sn',
                'invoice_date'
            ],
            request=self.request,
        )
        return context

    def get_links(self):
        result = []
        links = getattr(
            settings, 'MY_EQUIPMENT_LINKS', []
        )
        kwargs = {
            'username': self.request.user.username,
        }
        for link in links:
            result.append({
                'url': link['url'].format(**kwargs),
                'name': link['name']
            })
        return result

    def get_user(self):
        return self.request.user
