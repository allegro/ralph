# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from lck.django.common import nested_commit_on_success

from ralph.assets.forms import (
    AddDeviceForm, AddPartForm, EditDeviceForm,
    EditPartForm
)
from ralph.assets.models import (DeviceInfo, AssetSource, Asset, OfficeInfo)
from ralph.ui.views.common import Base
from ralph.assets.forms import SearchAssetForm


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
                href='/assets/dc',
            ),
            MenuItem(
                label='BackOffice',
                fugue_icon='fugue-printer',
                name='back_office',
                href='/assets/back_office',
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


class BackOfficeSearch(BackOfficeMixin):
    sidebar_selected = 'search'


class DataCenterSearch(DataCenterMixin):
    template_name = 'assets/search_asset.html'
    sidebar_selected = 'search'

    def get_context_data(self, *args, **kwargs):
        ret = super(DataCenterSearch, self).get_context_data(*args, **kwargs)
        self.data = Asset.objects.all()
        ret.update({
            'form': self.form,
            'data': self.data,
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = SearchAssetForm()
        self.data = Asset.objects.all()
        return super(DataCenterSearch, self).get(*args, **kwargs)


class AddDevice(Base):
    template_name = 'assets/add_device.html'

    def get_context_data(self, **kwargs):
        ret = super(AddDevice, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_device_asset_form',
            'edit_mode': False,
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = AddDeviceForm()
        return super(AddDevice, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = AddDeviceForm(self.request.POST)
        if self.form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            #FIXME: use 2 forms, with prefix=..., validate each other, 
            # and get given fields. don't join them.
            data = {}
            for field_name, field_value in self.form.cleaned_data.items():
                if field_name in ["barcode", "size", "sn", "warehouse"]:
                    continue
                if field_name == "model":
                    field_name = "%s_id" % field_name
                data[field_name] = field_value
            data['source'] = AssetSource.shipment
            serial_numbers = self.form.cleaned_data['sn']
            serial_numbers = filter(
                len, re.split(",|\n", serial_numbers))
            barcodes = self.form.cleaned_data['barcode']
            if barcodes:
                barcodes = filter(
                    len, re.split(",|\n", barcodes))
            i = 0
            duplicated_sn = []
            duplicated_barcodes = []
            for sn in serial_numbers:
                device_info = DeviceInfo(
                    warehouse_id=self.form.cleaned_data['warehouse'],
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
        return super(AddDevice, self).get(*args, **kwargs)


class BackOfficeAddDevice(AddDevice, BackOfficeMixin):
    sidebar_selected = 'add device'


class DataCenterAddDevice(AddDevice, DataCenterMixin):
    sidebar_selected = 'add device'


class AddPart(Base):
    template_name = 'assets/add_part.html'

    def get_context_data(self, **kwargs):
        ret = super(AddPart, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_part_form',
            'edit_mode': False,
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = AddPartForm()
        return super(AddPart, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = AddPartForm(self.request.POST)
        if self.form.is_valid():
            transaction.enter_transaction_management()
            transaction.managed()
            transaction.commit()
            data = {}
            for field_name, field_value in self.form.cleaned_data.items():
                if field_name in ["sn"]:
                    continue
                data[field_name] = field_value
            data['source'] = AssetSource.shipment
            serial_numbers = self.form.cleaned_data['sn']
            serial_numbers = filter(len, re.split(",|\n", serial_numbers))
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
        return super(AddPart, self).get(*args, **kwargs)


class BackOfficeAddPart(AddPart, BackOfficeMixin):
    sidebar_selected = 'add part'


class DataCenterAddPart(AddPart, DataCenterMixin):
    sidebar_selected = 'add part'


class EditDevice(Base):
    template_name = 'assets/edit_device_asset.html'

    def get_context_data(self, **kwargs):
        ret = super(EditDevice, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'edit_device_asset_form',
            'edit_mode': True,
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
            'warehouse': asset.device_info.warehouse.id,
            'size': asset.device_info.size,
        }
        if asset.office_info:
            initial_data.update({
                'license_key': asset.office_info.license_key,
                'version': asset.office_info.version,
                'unit_price': asset.office_info.unit_price,
                'license_type': asset.office_info.license_type,
                'date_of_last_inventory': asset.office_info.date_of_last_inventory,
                'last_logged_user': asset.office_info.last_logged_user,
            })
        self.form = EditDeviceForm(initial=initial_data)
        return super(EditDevice, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.form = EditDeviceForm(self.request.POST, self.request.FILES)
        if self.form.is_valid():
            asset.__dict__.update(**self.form.cleaned_data)
            if not asset.office_info:
                office_info = OfficeInfo()
            else:
                office_info = asset.office_info
            office_info.__dict__.update(**self.form.cleaned_data)
            office_info.save()
            asset.office_info = office_info
            asset.device_info.__dict__.update(**self.form.cleaned_data)
            asset.device_info.save()
            asset.save()
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditDevice, self).get(*args, **kwargs)


class EditPart(Base):
    template_name = 'assets/edit_part_asset.html'

    def get_context_data(self, **kwargs):
        ret = super(EditPart, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'edit_part_form',
            'edit_mode': True,
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
            'source': asset.source,
        }
        if asset.office_info:
            initial_data.update({
                'license_key': asset.office_info.license_key,
                'version': asset.office_info.version,
                'unit_price': asset.office_info.unit_price,
                'license_type': asset.office_info.license_type,
                'date_of_last_inventory': asset.office_info.date_of_last_inventory,
                'last_logged_user': asset.office_info.last_logged_user,
            })
        self.form = EditPartForm(initial=initial_data)
        return super(EditPart, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        asset = get_object_or_404(Asset, id=kwargs.get('asset_id'))
        self.form = EditPartForm(self.request.POST, self.request.FILES)
        if self.form.is_valid():
            asset.__dict__.update(**self.form.cleaned_data)
            if not asset.office_info:
                office_info = OfficeInfo()
            else:
                office_info = asset.office_info
            office_info.__dict__.update(**self.form.cleaned_data)
            office_info.save()
            asset.office_info = office_info
            asset.save()
        else:
            messages.error(self.request, _("Please correct the errors."))
        return super(EditPart, self).get(*args, **kwargs)
