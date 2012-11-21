#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.ui.widgets import DateWidget

from assets.models import AssetType, AssetModel, AssetStatus, LicenseTypes


def _all_assets_models():
    yield '', '---------'
    for asset_model in AssetModel.objects.all():
        yield asset_model.id, "%s %s" % (
            asset_model.manufacturer.name,
            asset_model.name,
        )


class BaseAssetForm(forms.Form):
    type = forms.ChoiceField(choices=AssetType(), label=_("Type"))
    model = forms.ChoiceField(choices=_all_assets_models(), label=_("Model"))
    invoice_no = forms.CharField(max_length=30)
    buy_date = forms.DateField(widget=DateWidget, label=_("Buy date"))
    support_period = forms.IntegerField(
        label=_("Support period in months"),
        min_value=0,
    )
    support_type = forms.CharField(label=_("Support type description"))
    support_void_reporting = forms.BooleanField(
        label=_("Support void reporting"),
        initial=True,
    )
    status = forms.ChoiceField(choices=AssetStatus(), label=_("Status"))


class BasePartAssetForm(BaseAssetForm):
    sn = forms.CharField(label=_("SN/SNs"), widget=forms.widgets.Textarea)


class BaseDeviceAssetForm(BaseAssetForm):
    barcode = forms.CharField(
        label=_("Barcode/Barcodes"),
        required=False,
        widget=forms.widgets.Textarea,
    )
    size = forms.IntegerField(label=_("Size"), min_value=1)
    location = forms.CharField(label=_("Location"), max_length=250)


def _validate_multivalue_data(data):
    error_msg = _("Field can't be empty. Please put the items separated "
                  "by new line or comma.")
    data = data.trim()
    if not data:
        raise forms.ValidationError(error_msg)
    if data.find(" ") > 0:
        raise forms.ValidationError(error_msg)
    if not filter(len, data.split("\n")) and not filter(len, data.split(",")):
        raise forms.ValidationError(error_msg)


class AddPartAssetForm(BasePartAssetForm):
    def clean_sn(self):
        data = self.cleaned_data["sn"]
        _validate_multivalue_data(data)
        return data


class AddDeviceAssetForm(BaseDeviceAssetForm):
    def clean_barcode(self):
        data = self.cleaned_data["barcode"]
        _validate_multivalue_data(data)
        return data


class OfficeAssetForm(forms.Form):
    license_key = forms.CharField(
        label=_("License key"),
        max_length=255,
        required=False,
    )
    version = forms.CharField(
        label=_("Version"),
        max_length=50,
        required=False,
    )
    order_no = forms.CharField(
        label=_("Order number"),
        max_length=50,
        required=False,
    )
    unit_price = forms.CharField(
        label=_("Unit price"),
        max_digits=20,
        decimal_places=2,
        initial=0,
    )
    attachment = forms.FileField(label=_("Attachment"), required=False)
    license_type = forms.ChoiceField(
        choices=LicenseTypes(),
        label=_("License type"),
        required=False,
    )
    date_of_last_inventory = forms.DateField(
        widget=DateWidget,
        required=False,
        label=_("Date of last inventory"),
    )
    last_logged_user = forms.CharField(
        label=_("Last logged user"),
        required=False,
        max_length=100,
    )


class EditPartAssetForm(BaseAssetForm, OfficeAssetForm):
    pass


class EditDeviceAssetForm(BaseAssetForm, OfficeAssetForm):
    pass

