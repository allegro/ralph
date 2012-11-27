#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django import forms
from django.forms import ModelForm, Form
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import (
    Asset, OfficeInfo, DeviceInfo, PartInfo, AssetStatus,
    AssetType
)
from ralph.ui.widgets import DateWidget
from ajax_select.fields import AutoCompleteSelectField
from ajax_select import make_ajax_field



class BaseAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'invoice_no', 'order_no',
            'buy_date', 'support_period', 'support_type',
            'support_void_reporting', 'provider', 'status',
            'sn', 'barcode', 'remarks',
        )
        widgets = {
            'sn': forms.widgets.Textarea(attrs={'rows': 25}),
            'barcode': forms.widgets.Textarea(attrs={'rows': 25}),
            'buy_date': DateWidget(),
            'remarks': forms.widgets.Textarea(attrs={'rows': 3}),
        }
    model = AutoCompleteSelectField(
        'asset_model', required=True,
        plugin_options=dict(add_link='/admin/assets/assetmodel/add/?name=')
    )

    def __init__(self, *args, **kwargs):
        mode = kwargs.get('mode')
        if mode:
            del kwargs['mode']
        super(BaseAssetForm, self).__init__(*args, **kwargs)
        if mode == "dc":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.DC.choices]
        elif mode == "back_office":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.BO.choices]


class BaseDeviceForm(ModelForm):
    class Meta:
        model = DeviceInfo
        fields = (
            'size', 'warehouse',
        )
    warehouse = AutoCompleteSelectField(
        'asset_warehouse', required=True,
        plugin_options=dict(add_link='/admin/assets/warehouse/add/?name=')
    )


class BasePartForm(ModelForm):
    class Meta:
        model = PartInfo
        fields = ('device', 'source_device', 'barcode_salvaged',)

    device = AutoCompleteSelectField(
        'asset_device', required=False,
        help_text='Enter barcode, sn, or model.'
    )
    source_device = AutoCompleteSelectField(
        'asset_device', required=False,
        help_text='Enter barcode, sn, or model.'
    )


def _validate_multivalue_data(data):
    error_msg = _("Field can't be empty. Please put the items separated "
                  "by new line or comma.")
    data = data.strip()
    if not data:
        raise forms.ValidationError(error_msg)
    if data.find(" ") > 0:
        raise forms.ValidationError(error_msg)
    if not filter(len, data.split("\n")) and not filter(len, data.split(",")):
        raise forms.ValidationError(error_msg)


class AddPartForm(BaseAssetForm):
    def clean_sn(self):
        data = self.cleaned_data["sn"]
        _validate_multivalue_data(data)
        return data


class AddDeviceForm(BaseAssetForm):
    def __init__(self, *args, **kwargs):
        super(AddDeviceForm, self).__init__(*args, **kwargs)

    def clean_sn(self):
        data = self.cleaned_data["sn"]
        _validate_multivalue_data(data)
        return data

    def clean_barcode(self):
        data = self.cleaned_data["barcode"].strip()
        sn_data = self.cleaned_data.get("sn", "").strip()
        if data:
            barcodes_count = len(filter(len, re.split(",|\n", data)))
            sn_count = len(filter(len, re.split(",|\n", sn_data)))
            if sn_count != barcodes_count:
                raise forms.ValidationError(_("Barcode list could be empty or "
                                              "must have the same number of "
                                              "items as a SN list."))
        return data


class OfficeForm(forms.ModelForm):
    class Meta:
        model = OfficeInfo
        exclude = ('created', 'modified')
        widgets = {
            'date_of_last_inventory': DateWidget(),
        }


class EditPartForm(BaseAssetForm):
    def __init__(self, *args, **kwargs):
        super(EditPartForm, self).__init__(*args, **kwargs)
        self.fields['sn'].widget = forms.widgets.TextInput()
        self.fields['sn'].label = _("SN")
        del self.fields['barcode']


class EditDeviceForm(BaseAssetForm):
    def __init__(self, *args, **kwargs):
        super(EditDeviceForm, self).__init__(*args, **kwargs)
        self.fields['sn'].widget = forms.widgets.TextInput()
        self.fields['sn'].label = _("SN")
        self.fields['barcode'].widget = forms.widgets.TextInput()
        self.fields['barcode'].label = _("Barcode")


class SearchAssetForm(Form):
    model = AutoCompleteSelectField(
        'asset_model',
        required=False,
        help_text=None
    )
    source_device = AutoCompleteSelectField(
        'asset_device',
        required=False,
    )

    invoice_no = forms.CharField(required=False)
    order_no = forms.CharField(required=False)
    buy_date = forms.DateField(required=False)
    provider = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False, choices=AssetStatus()
    )
    sn = forms.CharField(required=False)


