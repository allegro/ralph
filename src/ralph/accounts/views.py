# -*- coding: utf-8 -*-
from datetime import date
from urllib.parse import urlencode

import reversion
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from ralph.accounts.admin import AssetList, AssignedLicenceList, UserInfoMixin
from ralph.admin.mixins import RalphBaseTemplateView, RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.transitions.models import Transition
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
                '&emsp; <i class="fa fa-chevron-right" aria-hidden="true"></i> {} ({})'.format(  # noqa
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

    @staticmethod
    def _add_tags(request, asset, tags):
        asset.tags.add(*tags)
        with reversion.create_revision():
            asset.save()
            reversion.set_user(request.user)
            reversion.set_comment('Added tags {}'.format(', '.join(tags)))

    def _post_no(self, request, asset):
        tags = [settings.INVENTORY_TAG_MISSING]
        missing_asset_info = 'Please contact person responsible ' \
                             'for asset management'
        if settings.MISSING_ASSET_REPORT_URL is not None:
            missing_asset_info += '\n' + settings.MISSING_ASSET_REPORT_URL

        self._add_tags(request, asset, tags)
        messages.info(request, _(missing_asset_info))

    def _post_yes(self, request, asset):
        base_tag = settings.INVENTORY_TAG
        if asset.warehouse.stocktaking_tag_suffix != '':
            base_tag = '{prefix}-{warehouse}'.format(
                prefix=base_tag,
                warehouse=asset.warehouse.stocktaking_tag_suffix,
            )
        date_tag = None
        if settings.INVENTORY_TAG_APPEND_DATE:
            date_tag = '{base}_{date}'.format(
                base=base_tag,
                date=date.today().isoformat(),
            )

        tags = [
            base_tag,
            settings.INVENTORY_TAG_USER,
            date_tag,
        ]

        self._add_tags(request, asset, tags)
        messages.success(request, _('Successfully tagged asset'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = kwargs['answer']
        return context

    def post(self, request, *args, **kwargs):
        asset = get_object_or_404(BackOfficeAsset, id=request.POST['asset_id'])
        if(
            asset.user_id != request.user.id or
            not (
                asset.warehouse.stocktaking_enabled or
                asset.region.stocktaking_enabled
            )
        ):
            return HttpResponseForbidden()

        if request.POST['answer'] == 'yes':
            self._post_yes(request, asset)
        elif request.POST['answer'] == 'no':
            self._post_no(request, asset)

        return HttpResponseRedirect(reverse('current_user_info'))


class _AcceptanceProcessByCurrentUserMixin(object):
    _config = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG

    @property
    def acceptance_transition_id(self):
        return self._config['TRANSITION_ID']

    @property
    def back_office_status(self):
        return self._config['BACK_OFFICE_ACCEPT_STATUS']

    @property
    def acceptance_transition_exists(self):
        return Transition.objects.filter(
            id=self.acceptance_transition_id
        ).exists()

    def post(self, request, *args, **kwargs):
        assets_to_accept = self.get_assets_to_accept()
        admin_instance = ralph_site.get_admin_instance_for_model(
            BackOfficeAsset
        )
        url_name = admin_instance.get_transition_bulk_url_name()
        if assets_to_accept:
            url = reverse(url_name, args=(self.acceptance_transition_id,))
            query = urlencode([('select', a.id) for a in assets_to_accept])
            return HttpResponseRedirect('?'.join((url, query)))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['acceptance_transition_id'] = self.acceptance_transition_id
        context['acceptance_transition_exists'] = self.acceptance_transition_exists  # noqa: E501
        context['assets_to_accept'] = self.get_assets_to_accept()
        return context

    def get_assets_to_accept(self):
        return BackOfficeAsset.objects.filter(
            status=self.back_office_status
        ).filter(user=self.request.user)


class _DummyMixin(object):
    pass


AcceptAssetsForCurrentUserMixin = (
    _AcceptanceProcessByCurrentUserMixin
    if settings.ENABLE_ACCEPT_ASSETS_FOR_CURRENT_USER
    else _DummyMixin
)


class CurrentUserInfoView(
    AcceptAssetsForCurrentUserMixin,
    UserInfoMixin,
    RalphBaseTemplateView
):
    template_name = 'ralphuser/my_equipment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_equipment_links'] = self.get_links()
        asset_fields = [
            'user', ('barcode', _('Barcode / Inventory Number')),
            'model__category__name', 'model__manufacturer__name',
            'model__name', ('sn', _('Serial Number')), 'invoice_date', 'status'
        ]

        if settings.MY_EQUIPMENT_SHOW_BUYOUT_DATE:
            asset_fields += ['buyout_date']

        if settings.MY_EQUIPMENT_REPORT_FAILURE_URL:
            asset_fields += ['report_failure']

        warehouse_stocktaking_enabled = BackOfficeAsset.objects.filter(
            user=self.request.user, warehouse__stocktaking_enabled=True
        ).exists()
        region_stocktaking_enabled = BackOfficeAsset.objects.filter(
            user=self.request.user, region__stocktaking_enabled=True
        ).exists()

        if warehouse_stocktaking_enabled or region_stocktaking_enabled:
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

    def get_asset_queryset(self):
        qs = super().get_asset_queryset()
        return qs.select_related('user')
