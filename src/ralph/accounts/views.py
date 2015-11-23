# -*- coding: utf-8 -*-
from django.conf import settings
from django.views.generic import TemplateView

from ralph.accounts.admin import AssetList, AssignedLicenceList, UserInfoMixin
from ralph.admin.mixins import RalphTemplateView


class UserProfileView(RalphTemplateView):
    template_name = 'ralphuser/user_profile.html'


class CurrentUserInfoView(UserInfoMixin, TemplateView):
    template_name = 'ralphuser/my_equipment.html'

    def get_context_data(self, **kwargs):
        context = {}
        context['my_equipment_links'] = self.get_links()
        context['asset_list'] = AssetList(
            self.get_asset_queryset(),
            [
                'id', 'model__category__name', 'model__manufacturer__name',
                'model__name', 'sn', 'barcode', 'remarks', 'status'
            ],
            ['user_licence']
        )
        context['licence_list'] = AssignedLicenceList(
            self.get_licence_queryset(),
            ['id', 'software__name', 'niw']
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
