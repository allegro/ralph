#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from ralph.assets.forms import AddDeviceAssetForm, AddPartAssetForm
from ralph.assets.models import DeviceInfo, AssetSource, Asset
from ralph.ui.views.common import Base


class Index(Base):
    template_name = 'assets/base.html'


class AddDeviceAssets(Base):
    template_name = 'assets/add_device_assets.html'

    def get_context_data(self, **kwargs):
        ret = super(AddDeviceAssets, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_device_asset_form'
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


class AddPartAssets(Base):
    template_name = 'assets/add_part_assets.html'

    def get_context_data(self, **kwargs):
        ret = super(AddPartAssets, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_id': 'add_part_asset_form'
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
                msg = "Serial numbers with duplicates: %s. " % (
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

