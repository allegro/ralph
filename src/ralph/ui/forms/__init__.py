# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from django import forms

from ralph.business.models import RoleProperty
from ralph.ui.forms.util import all_ventures
from ralph.ui.widgets import DateWidget


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


class NetworksFilterForm(forms.Form):
    show_ip = forms.BooleanField(
        required=False,
        label="Show as addresses",
    )
    contains = forms.CharField(
        required=False, label="Contains",
        widget=forms.TextInput(attrs={'class': 'span12'}),
    )


class RolePropertyForm(forms.ModelForm):
    class Meta:
        model = RoleProperty
        widgets = {
            'role': forms.HiddenInput,
        }

    icons = {
        'symbol': 'fugue-hand-property',
        'type': 'fugue-property-blue',
    }

