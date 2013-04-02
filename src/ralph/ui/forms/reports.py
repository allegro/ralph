# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from ralph.ui.widgets import DateWidget
from ralph.ui.forms import all_ventures


class DevicesChoiceReportForm(forms.Form):
    deprecation = forms.ChoiceField(
        label="Devices after deprecation",
        widget=forms.CheckboxInput()
    )
    no_deprecation = forms.ChoiceField(
        label="Devices without deprecation date",
        widget=forms.CheckboxInput()
    )
    no_margin = forms.ChoiceField(
        label="Devices without deprecation margin",
        widget=forms.CheckboxInput()
    )
    no_support = forms.ChoiceField(
        label="Devices without support date",
        widget=forms.CheckboxInput()
    )
    no_purchase = forms.ChoiceField(
        label="Devices without purchase date",
        widget=forms.CheckboxInput()
    )
    no_venture = forms.ChoiceField(
        label="Devices without venture",
        widget=forms.CheckboxInput()
    )
    no_role = forms.ChoiceField(
        label="Devices without role",
        widget=forms.CheckboxInput()
    )
    no_parent = forms.ChoiceField(
        label="Devices without parent",
        widget=forms.CheckboxInput()
    )

    def get_initial(self):
        return super(DevicesChoiceReportForm, self).get_initial()


class SupportRangeReportForm(forms.Form):
    s_start = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='Start date',
    )
    s_end = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='End date',
    )


class DeprecationRangeReportForm(forms.Form):
    d_start = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='Start date',
    )
    d_end = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='End date',
    )


class WarrantyRangeReportForm(forms.Form):
    w_start = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='Start date',
    )
    w_end = forms.DateField(
        widget=DateWidget(
            attrs={'class': 'input-small'},
        ),
        label='End date',
    )


class ReportVentureCost(forms.Form):
    venture = forms.ChoiceField(label="Venture")

    def __init__(self, *args, **kwargs):
        super(ReportVentureCost, self).__init__(*args, **kwargs)
        self.fields['venture'].choices = all_ventures()


class ReportDeviceListForm(forms.Form):
    show_all_devices = forms.ChoiceField(
        label="Active devices",
        widget=forms.CheckboxInput()
    )
    show_all_deleted_devices = forms.ChoiceField(
        label="Deleted devices",
        widget=forms.CheckboxInput()
    )
