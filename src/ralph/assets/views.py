# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from lck.django.common import nested_commit_on_success
from ralph.assets.forms import (
    AddDeviceAssetForm, AddPartAssetForm, EditDeviceAssetForm,
    EditPartAssetForm)
from ralph.assets.models import (DeviceInfo, AssetSource, Asset, OfficeData)
from ralph.ui.views.common import Base


class AssetsMixin(Base):
    template_name = "assets/base.html"

    def get(self, *args, **kwargs):
        # TODO
        return super(AssetsMixin, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        # TODO
        return super(AssetsMixin, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetsMixin, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'mainmenu_items': self.get_mainmenu_items(),
            'section': 'assets',
            'sidebar_selected': self.sidebar_selected,
            'section': self.mainmenu_selected,
        })

        return ret

    def get_mainmenu_items(self):
        return [
            MenuItem(
                label='Data center',
                name='dc',
                fugue_icon='fugue-building',
                href='/assets/dc'
            ),
            MenuItem(
                label='BackOffice',
                fugue_icon='fugue-printer',
                name='back_office',
                href='/assets/back_office'
            ),
        ]


class DataCenterMixin(AssetsMixin):
    mainmenu_selected = 'dc'

    def get_sidebar_items(self):
        items = (
            ('/assets/dc/add/device/', 'Add device', 'fugue-block--plus'),
            ('/assets/dc/add/part/', 'Add part', 'fugue-block--plus'),
            ('/assets/dc/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Data center actions')] +
            [MenuItem(
             label=t[1],
             fugue_icon=t[2],
             href=t[0]
             ) for t in items]
        )
        return sidebar_menu


class BackOfficeMixin(AssetsMixin):
    mainmenu_selected = 'back_office'

    def get_sidebar_items(self):
        items = (
                ('/assets/back_office/add/device/', 'Add device',
                 'fugue-block--plus'),
                ('/assets/back_office/add/part/', 'Add part',
                 'fugue-block--plus'),
                ('/assets/back_office/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Back office actions')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in items]
        )
        return sidebar_menu


class DataCenterSearch(DataCenterMixin):
    sidebar_selected = 'search'


class BackOfficeSearch(BackOfficeMixin):
    sidebar_selected = 'search'


class AddDeviceAssets(Base):
    template_name = 'assets/add_device_assets.html'

    def get_context_data(self, **kwargs):
        ret = super(AddDeviceAssets, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_device_asset_form',
            'edit_mode': False
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = AddDeviceAssetForm()
        return super(AddDeviceAssets, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = AddDeviceAssetForm(self.request.POST)
        if self.form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            data = {}
            for field_name, field_value in self.form.cleaned_data.items():
                if field_name in ["barcode", "size", "sn", "magazine"]:
                    continue
                if field_name == "model":
                    field_name = "%s_id" % field_name
                data[field_name] = field_value
            data['source'] = AssetSource.shipment
            serial_numbers = self.form.cleaned_data['sn']
            if serial_numbers.find(",") != -1:
                serial_numbers = filter(len, serial_numbers.split(","))
            else:
                serial_numbers = filter(len, serial_numbers.split("\n"))
            barcodes = self.form.cleaned_data['barcode']
            if barcodes:
                if barcodes.find(",") > 0:
                    barcodes = filter(len, barcodes.split(","))
                else:
                    barcodes = filter(len, barcodes.split("\n"))
            i = 0
            duplicated_sn = []
            duplicated_barcodes = []
            for sn in serial_numbers:
                device_info = DeviceInfo(
                    magazine_id=self.form.cleaned_data['magazine'],
                    size=self.form.cleaned_data['size']
                )
                device_info.save()
                asset = Asset(
                    device_info=device_info,
                    sn=sn.strip(),
                    **data
                )
                if barcodes:
                    asset.barcode = barcodes[i].strip()
                try:
                    asset.save()
                except IntegrityError as e:
                    if "'sn'" in e[1]:
                        duplicated_sn.append(asset.sn)
                    if barcodes and "'barcode'" in e[1]:
                        duplicated_barcodes.append(asset.barcode)
                i += 1
            if duplicated_sn or duplicated_barcodes:
                transaction.rollback()
                msg = ""
                if duplicated_sn:
                    msg = "Serial numbers with duplicates: %s. " % (
                        ", ".join(duplicated_sn))
                if duplicated_barcodes:
                    msg += "Barcodes with duplicates: %s. " % (
                        ", ".join(duplicated_barcodes))
                messages.warning(self.request, msg)
            else:
                transaction.commit()
                transaction.managed(False)
                messages.success(self.request, _("Assets saved."))
                return HttpResponseRedirect('/assets/')
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddDeviceAssets, self).get(*args, **kwargs)


class BackOfficeAddDevice(AddDeviceAssets, BackOfficeMixin):
    sidebar_selected = 'add device'


class DataCenterAddDevice(AddDeviceAssets, DataCenterMixin):
    sidebar_selected = 'add device'


class AddPartAssets(Base):
    template_name = 'assets/add_part_assets.html'

    def get_context_data(self, **kwargs):
        ret = super(AddPartAssets, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_part_asset_form',
            'edit_mode': False
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = AddPartAssetForm()
        return super(AddPartAssets, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = AddPartAssetForm(self.request.POST)
        if self.form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            data = {}
            for field_name, field_value in self.form.cleaned_data.items():
                if field_name in ["sn"]:
                    continue
                if field_name == "model":
                    field_name = "%s_id" % field_name
                data[field_name] = field_value
            data['source'] = AssetSource.shipment
            serial_numbers = self.form.cleaned_data['sn']
            if serial_numbers.find(",") != -1:
                serial_numbers = filter(len, serial_numbers.split(","))
            else:
                serial_numbers = filter(len, serial_numbers.split("\n"))
            duplicated_sn = []
            for sn in serial_numbers:
                asset = Asset(
                    sn=sn.strip(),
                    **data
                )
                try:
                    asset.save()
                except IntegrityError as e:
                    if "'sn'" in e[1]:
                        duplicated_sn.append(asset.sn)
            if duplicated_sn:
                transaction.rollback()
                msg = "Serial numbers with duplicates: %s." % (
                    ", ".join(duplicated_sn))
                messages.warning(self.request, msg)
            else:
                transaction.commit()
                transaction.managed(False)
                messages.success(self.request, _("Assets saved."))
                return HttpResponseRedirect('/assets/')
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(AddPartAssets, self).get(*args, **kwargs)


class BackOfficeAddPart(AddPartAssets, BackOfficeMixin):
    sidebar_selected = 'add part'


class DataCenterAddPart(AddPartAssets, DataCenterMixin):
    sidebar_selected = 'add part'


class EditDeviceAsset(Base):
    template_name = 'assets/edit_device_asset.html'

    def get_context_data(self, **kwargs):
        ret = super(EditDeviceAsset, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'edit_device_asset_form',
            'edit_mode': True
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if not asset.device_info:  # it isn't device asset
            raise Http404()
        initial_data = {
            'type': asset.type,
            'model': asset.model.id,
            'invoice_no': asset.invoice_no,
            'order_no': asset.order_no,
            'buy_date': asset.buy_date,
            'support_period': asset.support_period,
            'support_type': asset.support_type,
            'support_void_reporting': asset.support_void_reporting,
            'provider': asset.provider,
            'status': asset.status,
            'sn': asset.sn,
            'source': asset.source,
            'barcode': asset.barcode,
            'magazine': asset.device_info.magazine.id,
            'size': asset.device_info.size
        }
        if asset.office_data:
            initial_data.update({
                'license_key': asset.office_data.license_key,
                'version': asset.office_data.version,
                'unit_price': asset.office_data.unit_price,
                'license_type': asset.office_data.license_type,
                'date_of_last_inventory': asset.office_data.date_of_last_inventory,
                'last_logged_user': asset.office_data.last_logged_user
            })
        self.form = EditDeviceAssetForm(initial=initial_data)
        return super(EditDeviceAsset, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.form = EditDeviceAssetForm(self.request.POST, self.request.FILES)
        if self.form.is_valid():
            asset.__dict__.update(**self.form.cleaned_data)
            if not asset.office_data:
                office_data = OfficeData()
            else:
                office_data = asset.office_data
            office_data.__dict__.update(**self.form.cleaned_data)
            office_data.save()
            asset.office_data = office_data
            asset.device_info.__dict__.update(**self.form.cleaned_data)
            asset.device_info.save()
            asset.save()
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditDeviceAsset, self).get(*args, **kwargs)


class EditPartAsset(Base):
    template_name = 'assets/edit_part_asset.html'

    def get_context_data(self, **kwargs):
        ret = super(EditPartAsset, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'edit_part_asset_form',
            'edit_mode': True
        })
        return ret

    def get(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        if asset.device_info:  # it isn't part asset
            raise Http404()
        initial_data = {
            'type': asset.type,
            'model': asset.model.id,
            'invoice_no': asset.invoice_no,
            'order_no': asset.order_no,
            'buy_date': asset.buy_date,
            'support_period': asset.support_period,
            'support_type': asset.support_type,
            'support_void_reporting': asset.support_void_reporting,
            'provider': asset.provider,
            'status': asset.status,
            'sn': asset.sn,
            'source': asset.source
        }
        if asset.office_data:
            initial_data.update({
                'license_key': asset.office_data.license_key,
                'version': asset.office_data.version,
                'unit_price': asset.office_data.unit_price,
                'license_type': asset.office_data.license_type,
                'date_of_last_inventory': asset.office_data.date_of_last_inventory,
                'last_logged_user': asset.office_data.last_logged_user
            })
        self.form = EditPartAssetForm(initial=initial_data)
        return super(EditPartAsset, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.form = EditPartAssetForm(self.request.POST, self.request.FILES)
        if self.form.is_valid():
            asset.__dict__.update(**self.form.cleaned_data)
            if not asset.office_data:
                office_data = OfficeData()
            else:
                office_data = asset.office_data
            office_data.__dict__.update(**self.form.cleaned_data)
            office_data.save()
            asset.office_data = office_data
            asset.save()
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditPartAsset, self).get(*args, **kwargs)

