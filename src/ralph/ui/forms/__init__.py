# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ajax_select.fields import AutoCompleteField, AutoCompleteSelectField
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.business.models import RoleProperty
from ralph.ui.forms.util import all_ventures
from ralph.ui.widgets import DateWidget


class VentureServiceFilterForm(forms.Form):
    venture = AutoCompleteField(
        ('ralph.ui.channels', 'VentureLookup'),
        required=False,
        label=_('Venture'),
        help_text='Filter by venture',
    )
    service = AutoCompleteField(
        ('ralph.ui.channels', 'ServiceCatalogLookup'),
        required=False,
        label=_('Service catalog'),
        help_text='Filter by service',
    )


class DateRangeForm(forms.Form):
    start = forms.DateField(widget=DateWidget, label='Start date')
    end = forms.DateField(widget=DateWidget, label='End date')


class MarginsReportForm(DateRangeForm):
    margin_venture = forms.ChoiceField()

    def __init__(self, margin_kinds, *args, **kwargs):
        super(MarginsReportForm, self).__init__(*args, **kwargs)
        for mk in margin_kinds:
            field_id = 'm_%d' % mk.id
            field = forms.IntegerField(
                label='',
                initial=mk.margin,
                required=False,
                widget=forms.TextInput(
                    attrs={
                        'class': 'span12',
                        'style': 'text-align: right',
                    }
                )
            )
            field.initial = mk.margin
            self.fields[field_id] = field
        self.fields['margin_venture'].choices = all_ventures()

    def get(self, field):
        try:
            return self.cleaned_data[field]
        except (KeyError, AttributeError):
            try:
                return self.initial[field]
            except KeyError:
                return self.fields[field].initial


class VentureFilterForm(forms.Form):
    show_all = forms.BooleanField(
        required=False,
        label="Show all ventures",
    )


class RolePropertyForm(forms.ModelForm):

    class Meta:
        model = RoleProperty
        widgets = {
            'role': forms.HiddenInput,
            'venture': forms.HiddenInput,
            'default': forms.TextInput,
        }

    icons = {
        'symbol': 'fugue-hand-property',
        'type': 'fugue-property-blue',
    }


class ChooseAssetForm(forms.Form):
    asset = AutoCompleteSelectField(
        ('ralph_assets.api_ralph', 'AssetLookup'),
        required=False,  # handled by clean_asset
    )

    def __init__(self, device_id, *args, **kwargs):
        super(ChooseAssetForm, self).__init__(*args, **kwargs)
        self.fields['asset'].widget.show_help_text = False
        self.device_id = device_id

    def clean_asset(self):
        asset = self.cleaned_data['asset']
        if not asset:
            raise forms.ValidationError(
                "You cannot save this field without selecting an asset. "
                "If you want to unlink an asset from this device, "
                "please use 'Edit this asset' button below."
            )
        if 'ralph_assets' in settings.INSTALLED_APPS:
            from ralph_assets.api_ralph import is_asset_assigned
            if is_asset_assigned(
                asset_id=asset.id,
                exclude_devices=[self.device_id],
            ):
                raise forms.ValidationError(
                    "This asset is already linked to some other device. "
                    "To resolve this conflict, please click the link above."
                )
            return asset
