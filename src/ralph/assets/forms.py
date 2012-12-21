#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from ajax_select.fields import AutoCompleteSelectField, AutoCompleteField
from django.forms import (
    ModelForm, Form, CharField, DateField, ChoiceField, ValidationError,
    IntegerField,
)
from django import forms

from django.forms.widgets import Textarea, HiddenInput
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import (
    Asset, OfficeInfo, DeviceInfo, PartInfo, AssetStatus, AssetType,
)
from ralph.ui.widgets import DateWidget, HiddenSelectWidget

from django.utils.html import escape
from django.utils.safestring import mark_safe


class CodeWidget(forms.TextInput):
    def render(self, name, value, attrs=None, choices=()):
        formatted = escape(value) if value else ''
        return mark_safe('''
        <div class='code_field' id="id_%s" name="%s" width=200 height=500 style='width:200px;height:500px;' >
        %s</div>''' % (
            escape(name), escape(name), formatted))

class ModeNotSetException(Exception):
    pass


class BaseAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'invoice_no', 'order_no', 'request_date',
            'delivery_date', 'invoice_date', 'production_use_date',
            'provider_order_date', 'price', 'support_price', 'support_period',
            'support_type', 'support_void_reporting', 'provider', 'status',
            'remarks', 'sn', 'barcode', 'warehouse',
        )
        widgets = {
            'remarks': Textarea(attrs={'rows': 3}),
            'support_type': Textarea(attrs={'rows': 5}),
        }
    model = AutoCompleteSelectField(
        'asset_model',
        required=True,
        plugin_options=dict(add_link='/admin/assets/assetmodel/add/?name=')
    )
    warehouse = AutoCompleteSelectField(
        'asset_warehouse',
        required=True,
        plugin_options=dict(add_link='/admin/assets/warehouse/add/?name=')
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


class BarcodeField(CharField):
    def to_python(self, value):
        return value if value else None


class BulkEditAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'device_info', 'invoice_no', 'order_no',
            'request_date', 'delivery_date', 'invoice_date',
            'production_use_date', 'provider_order_date',
            'provider_order_date', 'sn', 'barcode', 'price', 'support_price',
            'support_period', 'support_type', 'support_void_reporting',
            'provider', 'source', 'status',
        )
        widgets = {
            'invoice_date': DateWidget(attrs={
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
            }),
            'device_info': HiddenSelectWidget(),
        }
    barcode = BarcodeField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super(BulkEditAssetForm, self).__init__(*args, **kwargs)
        fillable_fields = [
            'type', 'model', 'device_info', 'invoice_no', 'order_no',
            'request_date', 'delivery_date', 'invoice_date',
            'production_use_date', 'provider_order_date',
            'provider_order_date', 'support_period', 'support_type',
            'provider', 'source', 'status',
        ]
        for field_name in self.fields:
            if field_name in fillable_fields:
                classes = "span12 fillable"
            elif field_name == 'support_void_reporting':
                classes = ""
            else:
                classes = "span12"
            self.fields[field_name].widget.attrs = {'class': classes}


class DeviceForm(ModelForm):
    class Meta:
        model = DeviceInfo
        fields = (
            'size',
        )

    def clean_size(self):
        size = self.cleaned_data.get('size')
        if size not in range(0, 65536):
            raise ValidationError(
                _("Invalid size, use range 0 to 65535")
            )
        return size


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
            channel,
            required=False,
            help_text='Enter barcode, sn, or model.',
        )
        self.fields['source_device'] = AutoCompleteSelectField(
            channel,
            required=False,
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
    items = []
    for item in filter(len, re.split(",|\n", data)):
        item = item.strip()
        if item in items:
            raise ValidationError(
                _("There are duplicate serial numbers in field.")
            )
        elif ' ' in item:
            raise ValidationError(
                _("Serial number can't contain white characters.")
            )
        elif item:
            items.append(item)
    if not items:
        raise ValidationError(error_msg)
    return items


def _check_serial_numbers_uniqueness(serial_numbers):
    assets = Asset.objects.filter(sn__in=serial_numbers)
    if not assets:
        return True, []
    not_unique = []
    for asset in assets:
        not_unique.append((asset.sn, asset.id, asset.type))
    return False, not_unique


def _check_barcodes_uniqueness(barcodes):
    assets = Asset.objects.filter(barcode__in=barcodes)
    if not assets:
        return True, []
    not_unique = []
    for asset in assets:
        not_unique.append((asset.barcode, asset.id, asset.type))
    return False, not_unique


def _sn_additional_validation(serial_numbers):
    is_unique, not_unique_sn = _check_serial_numbers_uniqueness(serial_numbers)
    if not is_unique:
        # ToDo: links to assets with duplicate sn
        msg = "Following serial number already exists in DB: %s" % (
            ", ".join(item[0] for item in not_unique_sn)
        )
        raise ValidationError(msg)


class BaseAddAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'warehouse', 'invoice_no', 'order_no', 'price', 'support_period',
            'support_type', 'support_void_reporting', 'provider', 'status',
            'remarks', 'request_date',
            'provider_order_date', 'delivery_date', 'invoice_date',
            'production_use_date', 'provider_order_date',
        )
        widgets = {
            'request_date': DateWidget(),
            'delivery_date': DateWidget(),
            'invoice_date': DateWidget(),
            'production_use_date': DateWidget(),
            'provider_order_date': DateWidget(),
            'remarks': Textarea(attrs={'rows': 3}),
            'support_type': Textarea(attrs={'rows': 5}),
        }
    model = AutoCompleteSelectField(
        'asset_model',
        required=True,
        plugin_options=dict(add_link='/admin/assets/assetmodel/add/?name=')
    )
    warehouse = AutoCompleteSelectField(
        'asset_warehouse',
        required=True,
        plugin_options=dict(add_link='/admin/assets/warehouse/add/?name=')
    )

    def __init__(self, *args, **kwargs):
        mode = kwargs.get('mode')
        if mode:
            del kwargs['mode']
        super(BaseAddAssetForm, self).__init__(*args, **kwargs)
        if mode == "dc":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.DC.choices]
        elif mode == "back_office":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.BO.choices]


class BaseEditAssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = (
            'type', 'model', 'invoice_no', 'order_no', 'request_date',
            'delivery_date', 'invoice_date', 'production_use_date',
            'provider_order_date', 'support_period', 'support_type',
            'support_void_reporting', 'provider', 'status',
            'remarks', 'sn', 'barcode', 'warehouse'
        )
        widgets = {
            'request_date': DateWidget(),
            'delivery_date': DateWidget(),
            'invoice_date': DateWidget(),
            'production_use_date': DateWidget(),
            'provider_order_date': DateWidget(),
            'remarks': Textarea(attrs={'rows': 3}),
            'support_type': Textarea(attrs={'rows': 5}),
            'sn': Textarea(attrs={'rows': 25}),
            'barcode': Textarea(attrs={'rows': 1}),
        }
    model = AutoCompleteSelectField(
        'asset_model',
        required=True,
        plugin_options=dict(add_link='/admin/assets/assetmodel/add/?name=')
    )
    warehouse = AutoCompleteSelectField(
        'asset_warehouse',
        required=True,
        plugin_options=dict(add_link='/admin/assets/warehouse/add/?name=')
    )

    def __init__(self, *args, **kwargs):
        mode = kwargs.get('mode')
        if mode:
            del kwargs['mode']
        super(BaseEditAssetForm, self).__init__(*args, **kwargs)
        if mode == "dc":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.DC.choices]
        elif mode == "back_office":
            self.fields['type'].choices = [
                (c.id, c.desc) for c in AssetType.BO.choices]

    def clean_sn(self):
        return self.instance.sn


class AddPartForm(BaseAddAssetForm):
    sn = CharField(
        label=_("SN/SNs"), required=True, widget=Textarea(attrs={'rows': 25}),
    )

    def clean_sn(self):
        data = _validate_multivalue_data(self.cleaned_data["sn"])
        _sn_additional_validation(data)
        return data


class AddDeviceForm(BaseAddAssetForm):
    sn = CharField(
        label=_("SN/SNs"), required=True, widget=Textarea(attrs={'rows': 25}),
    )
    barcode = CharField(
        label=_("Barcode/Barcodes"), required=False,
        widget=Textarea(attrs={'rows': 25}),
    )

    def __init__(self, *args, **kwargs):
        super(AddDeviceForm, self).__init__(*args, **kwargs)

    def clean_sn(self):
        data = _validate_multivalue_data(self.cleaned_data["sn"])
        _sn_additional_validation(data)
        return data

    def clean_barcode(self):
        data = self.cleaned_data["barcode"].strip()
        barcodes = []
        if data:
            for barcode in filter(len, re.split(",|\n", data)):
                barcode = barcode.strip()
                if barcode in barcodes:
                    raise ValidationError(
                        _("There are duplicate barcodes in field.")
                    )
                elif ' ' in barcode:
                    raise ValidationError(
                        _("Serial number can't contain white characters.")
                    )
                elif barcode:
                    barcodes.append(barcode)
            if not barcodes:
                raise ValidationError(_("Barcode list could be empty or "
                                        "must have the same number of "
                                        "items as a SN list."))
            is_unique, not_unique_bc = _check_barcodes_uniqueness(barcodes)
            if not is_unique:
                # ToDo: links to assets with duplicate barcodes
                msg = "Following barcodes already exists in DB: %s" % (
                    ", ".join(item[0] for item in not_unique_bc)
                )
                raise ValidationError(msg)
        return barcodes

    def clean(self):
        cleaned_data = super(AddDeviceForm, self).clean()
        serial_numbers = cleaned_data.get("sn", [])
        barcodes = cleaned_data.get("barcode", [])
        if barcodes and len(serial_numbers) != len(barcodes):
            self._errors["barcode"] = self.error_class([
                _("Barcode list could be empty or must have the same number "
                  "of items as a SN list.")
            ])
        return cleaned_data


class OfficeForm(ModelForm):
    class Meta:
        model = OfficeInfo
        exclude = ('created', 'modified')
        widgets = {
            'date_of_last_inventory': DateWidget(),
        }


class EditPartForm(BaseEditAssetForm):
    pass


class EditDeviceForm(BaseEditAssetForm):
    pass


class SearchAssetForm(Form):
    """returns search asset form for DC and BO.

    :param mode: one of `dc` for DataCenter or `bo` for Back Office
    :returns Form
    """
    model = AutoCompleteField(
        'asset_model',
        required=False,
        help_text=None,
    )
    invoice_no = CharField(required=False)
    order_no = CharField(required=False)
    invoice_date_from = DateField(
        required=False, widget=DateWidget(attrs={
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label="Invoice date",
    )
    invoice_date_to = DateField(
        required=False, widget=DateWidget(attrs={
            'class': 'end-date-field ',
            'placeholder': 'End YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='')
    provider = CharField(required=False, label='Provider')
    status = ChoiceField(
        required=False, choices=[('', '----')] + AssetStatus(),
        label='Status'
    )
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
            required=False,
        )


class DeleteAssetConfirmForm(Form):
    asset_id = IntegerField(widget=HiddenInput())
