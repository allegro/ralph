# -*- coding: utf-8 -*-
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from ralph.accounts.admin import AssetList, AssignedLicenceList, UserInfoMixin
from ralph.admin.mixins import RalphBaseTemplateView, RalphTemplateView
from ralph.back_office.models import BackOfficeAsset
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


class InventoryTagConfirmationView(RalphBaseTemplateView):
    template_name = 'ralphuser/inventory_tag_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_fields = [
            ('barcode', _('Barcode / Inventory Number')),
            'model__category__name', 'model__manufacturer__name',
            'model__name', ('sn', _('Serial Number'))
        ]

        context['asset_details'] = MyEquipmentAssetList(
            BackOfficeAsset.objects.filter(id=self.kwargs['asset_id']),
            asset_fields,
            request=self.request
        )
        return context


class InventoryTagView(View):
    http_method_names = ['post']

    def _post_no(self, request, asset):
        asset.tags.add(
            settings.INVENTORY_TAG_MISSING
        )
        missing_asset_info = 'Please contact person responsible ' \
                             'for asset management'
        if settings.MISSING_ASSET_REPORT_URL is not None:
            missing_asset_info += '\n' + settings.MISSING_ASSET_REPORT_URL

        asset.save()
        messages.info(request, _(missing_asset_info))

    def _post_yes(self, request, asset):
        date_tag = None
        if settings.INVENTORY_TAG_APPEND_DATE:
            date_tag = settings.INVENTORY_TAG + '_' + date.today().isoformat()

        asset.tags.add(
            settings.INVENTORY_TAG,
            settings.INVENTORY_TAG_USER,
            date_tag
        )

        asset.save()
        messages.success(request, _('Successfully tagged asset'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = kwargs['answer']
        return context

    def post(self, request, *args, **kwargs):
        asset = get_object_or_404(BackOfficeAsset, id=request.POST['asset_id'])
        if(asset.user_id != request.user.id
                or (not asset.warehouse.stocktaking_enabled
                    and request.user.regions.filter(
                        stocktaking_enabled=True
                    ).count() == 0)):
            return HttpResponseForbidden()

        if request.POST['answer'] == 'yes':
            self._post_yes(request, asset)
        elif request.POST['answer'] == 'no':
            self._post_no(request, asset)

        return HttpResponseRedirect(reverse('current_user_info'))


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

        if BackOfficeAsset.objects.filter(
                user=self.request.user, warehouse__stocktaking_enabled=True
        ).count() > 0\
                or self.request.user.regions.filter(
                    stocktaking_enabled=True
                ).count() > 0:
            asset_fields += ['confirm_ownership']

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
