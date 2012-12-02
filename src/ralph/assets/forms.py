#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.core.validators import MaxLengthValidator
from ajax_select.fields import AutoCompleteSelectField
from django.forms import (
    ModelForm, Form, CharField, DateField, ChoiceField, ValidationError,
    IntegerField,
)
from django.forms.widgets import Textarea, TextInput, HiddenInput
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import (
    Asset, OfficeInfo, DeviceInfo, PartInfo, AssetStatus, AssetType,
)
from ralph.ui.widgets import DateWidget, HiddenSelectWidget


class ModeNotSetException(Exception):
    pass


class BaseAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'invoice_no', 'order_no',
            'buy_date', 'support_period', 'support_type',
            'support_void_reporting', 'provider', 'status',
            'remarks',
        )
        widgets = {
            'sn': Textarea(attrs={'rows': 25}),
            'barcode': Textarea(attrs={'rows': 25}),
            'buy_date': DateWidget(),
            'remarks': Textarea(attrs={'rows': 3}),
        }
    model = AutoCompleteSelectField(
        'asset_model', required=True,
        plugin_options=dict(add_link='/admin/assets/assetmodel/add/?name=')
    )
    sn = CharField(required=True, widget=Textarea(attrs={'rows': 25}))
    barcode = CharField(required=False, widget=Textarea(attrs={'rows': 25}))

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


class BarcodeField(CharField):
    def to_python(self, value):
        return value if value else None


class BulkEditAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'device_info', 'invoice_no', 'order_no',
            'buy_date', 'sn', 'barcode', 'support_period', 'support_type',
            'support_void_reporting', 'provider', 'source', 'status',
        )
        widgets = {
            'buy_date': DateWidget(),
            'device_info': HiddenSelectWidget(),
        }
    barcode = BarcodeField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super(BulkEditAssetForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs = {'class': 'span12'}


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
        fields = ('barcode_salvaged',)

    def __init__(self, *args, **kwargs):
        """mode argument is required for distinguish ajax sources"""
        mode = kwargs.get('mode')
        if mode:
            del kwargs['mode']
        else:
            raise ModeNotSetException("mode argument not given.")
        super(BasePartForm, self).__init__(*args, **kwargs)

        channel = 'asset_dcdevice' if mode == 'dc' else 'asset_bodevice'
        self.fields['device'] = AutoCompleteSelectField(
            channel, required=False,
            help_text='Enter barcode, sn, or model.',
        )
        self.fields['source_device'] = AutoCompleteSelectField(
            channel, required=False,
            help_text='Enter barcode, sn, or model.',
        )
        if self.instance.source_device:
            self.fields[
                'source_device'
            ].initial = self.instance.source_device.id
        if self.instance.device:
            self.fields['device'].initial = self.instance.device.id


def _validate_multivalue_data(data):
    error_msg = _("Field can't be empty. Please put the items separated "
                  "by new line or comma.")
    data = data.strip()
    if not data:
        raise ValidationError(error_msg)
    if data.find(" ") > 0:
        raise ValidationError(error_msg)
    if not filter(len, data.split("\n")) and not filter(len, data.split(",")):
        raise ValidationError(error_msg)


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
                raise ValidationError(_("Barcode list could be empty or "
                                        "must have the same number of "
                                        "items as a SN list."))
        return data


class OfficeForm(ModelForm):
    class Meta:
        model = OfficeInfo
        exclude = ('created', 'modified')
        widgets = {
            'date_of_last_inventory': DateWidget(),
        }


class EditPartForm(BaseAssetForm):
    def __init__(self, *args, **kwargs):
        super(EditPartForm, self).__init__(*args, **kwargs)
        self.fields['sn'].widget = TextInput()
        self.fields['sn'].label = _("SN")
        self.fields['sn'].validators = [MaxLengthValidator(200), ]
        if self.instance.sn:
            self.fields['sn'].initial = self.instance.sn
        del self.fields['barcode']


class EditDeviceForm(BaseAssetForm):
    def __init__(self, *args, **kwargs):
        super(EditDeviceForm, self).__init__(*args, **kwargs)
        self.fields['sn'].widget = TextInput()
        self.fields['sn'].label = _("SN")
        self.fields['sn'].validators = [MaxLengthValidator(200), ]
        if self.instance.sn:
            self.fields['sn'].initial = self.instance.sn
        self.fields['barcode'].widget = TextInput()
        self.fields['barcode'].label = _("Barcode")
        self.fields['barcode'].validators = [MaxLengthValidator(200), ]
        if self.instance.barcode:
            self.fields['barcode'].initial = self.instance.barcode


class SearchAssetForm(Form):
    """returns search asset form for DC and BO.

    :param mode: one of `dc` for DataCenter or `bo` for Back Office
    :returns Form
    """

    model = AutoCompleteSelectField(
        'asset_model',
        required=False,
        help_text=None
    )

    invoice_no = CharField(required=False)
    order_no = CharField(required=False)
    buy_date_from = DateField(
        required=False, widget=DateWidget(),
        label="Buy date from",
    )
    buy_date_to = DateField(
        required=False, widget=DateWidget(),
        label="Buy date to")
    provider = CharField(required=False, label='Provider')
    status = ChoiceField(required=False, choices=AssetStatus(), label='Status')
    sn = CharField(required=False, label='SN')

    def __init__(self, *args, **kwargs):
        # Ajax sources are different for DC/BO, use mode for distinguish
        mode = kwargs.get('mode')
        if mode:
            del kwargs['mode']
        channel = 'asset_dcdevice' if mode == 'dc' else 'asset_bodevice'
        super(SearchAssetForm, self).__init__(*args, **kwargs)
        self.fields['device'] = AutoCompleteSelectField(
            channel,
            required=False
        )


class DeleteAssetConfirmForm(Form):
    asset_id = IntegerField(widget=HiddenInput())

