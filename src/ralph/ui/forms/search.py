# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

from django import forms
from lck.django.choices import Choices

from ralph.discovery.models import DeviceType, DeprecationKind
from ralph.ui.widgets import (
    DateWidget,
    DeviceGroupWidget,
    ComponentGroupWidget,
)


def validate_start_end_date_date(start, end):
    if start and end and start > end:
        raise forms.ValidationError(
            "The end date has to be later than the start date"
        )


class TooltipContent(Choices):
    _ = Choices.Choice

    empty_field = _('Enter "none" to search for empty fields')
    empty_field_venture = _('Enter "none" or "-" to search for empty fields')
    software_field = _(
        'Enter "package_name" or "package_name operator version" to search '
        'software package. Operators list: " > >= < <= == " and "^=" for '
        'startswith version. Example: "Apache<=2.4.4"'
    )


class SearchForm(forms.Form):
    name = forms.CharField(required=False,
                           widget=forms.TextInput(attrs={'class': 'span12'}))
    address = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={
                                  'class': 'span12',
                                  'title': TooltipContent.empty_field,
                              }),
                              label="Address or network")
    remarks = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={
                                  'class': 'span12',
                                  'title': TooltipContent.empty_field
                              }))
    role = forms.CharField(required=False,
                           widget=forms.TextInput(attrs={
                               'class': 'span12',
                               'title': TooltipContent.empty_field,
                           }),
                           label="Venture or role")
    model = forms.CharField(required=False,
                            widget=forms.TextInput(attrs={
                                'class': 'span12',
                                'title': TooltipContent.empty_field_venture,
                            }))
    component = forms.CharField(required=False,
                                widget=forms.TextInput(
                                    attrs={'class': 'span12'}),
                                label="Component")
    software = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={
                                   'class': 'span12',
                                   'title': TooltipContent.software_field,
                               }),
                               label="Software")
    serial = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={
                                 'class': 'span12',
                                 'title': TooltipContent.empty_field,
                             }),
                             label="Serial number, MAC or WWN")
    barcode = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={
                                  'class': 'span12',
                                  'title': TooltipContent.empty_field,
                              }))
    position = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={
                                   'class': 'span12',
                                   'title': TooltipContent.empty_field,
                               }),
                               label="Datacenter, rack or position")
    history = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={
                                  'class': 'span12'
                              }))
    device_type = forms.MultipleChoiceField(required=False,
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'span12'}),
                                            choices=DeviceType(
                                                item=lambda e: (e.id, e.raw)),
                                            )
    device_group = forms.IntegerField(required=False,
                                      widget=DeviceGroupWidget, label="")
    component_group = forms.IntegerField(required=False,
                                         widget=ComponentGroupWidget, label="")
    purchase_date_start = forms.DateField(required=False,
                                          widget=DateWidget(attrs={
                                              'class': 'span12',
                                              'placeholder': 'Start YYYY-MM-DD',
                                              'data-collapsed': True,
                                          }),
                                          label='Purchase date', input_formats=['%Y-%m-%d'])
    purchase_date_end = forms.DateField(required=False,
                                        widget=DateWidget(attrs={
                                            'class': 'span12 end-date-field',
                                            'placeholder': 'End YYYY-MM-DD',
                                            'data-collapsed': True,
                                        }),
                                        label='', input_formats=['%Y-%m-%d'])
    no_purchase_date = forms.BooleanField(required=False,
                                          label="Empty purchase date",
                                          widget=forms.CheckboxInput(attrs={
                                              'data-collapsed': True,
                                          }))
    deprecation_date_start = forms.DateField(required=False,
                                             widget=DateWidget(attrs={
                                                 'class': 'span12',
                                                 'placeholder': 'Start YYYY-MM-DD',
                                                 'data-collapsed': True,
                                             }),
                                             label='Deprecation date', input_formats=['%Y-%m-%d'])
    deprecation_date_end = forms.DateField(required=False,
                                           widget=DateWidget(attrs={
                                               'class': 'span12 end-date-field',
                                               'placeholder': 'End YYYY-MM-DD',
                                               'data-collapsed': True,
                                           }),
                                           label='', input_formats=['%Y-%m-%d'])
    no_deprecation_date = forms.BooleanField(required=False,
                                             label="Empty deprecation date",
                                             widget=forms.CheckboxInput(attrs={
                                                 'data-collapsed': True,
                                             }))
    deprecation_kind = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'span12',
                   'data-collapsed': True},),
        label="Deprecation",
        choices=[('None', '-----')] + [(kind.id, kind.name)
                                       for kind in DeprecationKind.objects.all()],
    )
    warranty_expiration_date_start = forms.DateField(required=False,
                                                     widget=DateWidget(attrs={
                                                         'class': 'span12',
                                                         'placeholder': 'Start YYYY-MM-DD',
                                                         'data-collapsed': True,
                                                     }),
                                                     label='Warranty expiration date', input_formats=['%Y-%m-%d'])
    warranty_expiration_date_end = forms.DateField(required=False,
                                                   widget=DateWidget(attrs={
                                                       'class': 'span12 end-date-field',
                                                       'placeholder': 'End YYYY-MM-DD',
                                                       'data-collapsed': True,
                                                   }),
                                                   label='', input_formats=['%Y-%m-%d'])
    no_warranty_expiration_date = forms.BooleanField(required=False,
                                                     label="Empty warranty expiration date",
                                                     widget=forms.CheckboxInput(attrs={
                                                         'data-collapsed': True,
                                                     }))
    support_expiration_date_start = forms.DateField(required=False,
                                                    widget=DateWidget(attrs={
                                                        'class': 'span12',
                                                        'placeholder': 'Start YYYY-MM-DD',
                                                        'data-collapsed': True,
                                                    }),
                                                    label='Support expiration date', input_formats=['%Y-%m-%d'])
    support_expiration_date_end = forms.DateField(required=False,
                                                  widget=DateWidget(attrs={
                                                      'class': 'span12 end-date-field ',
                                                      'placeholder': 'End YYYY-MM-DD',
                                                      'data-collapsed': True,
                                                  }),
                                                  label='', input_formats=['%Y-%m-%d'])
    no_support_expiration_date = forms.BooleanField(required=False,
                                                    label="Empty support expiration date",
                                                    widget=forms.CheckboxInput(attrs={
                                                        'data-collapsed': True,
                                                    }))
    with_changes = forms.BooleanField(
        required=False,
        label="Only with Scan changes",
    )
    deleted = forms.BooleanField(required=False, label="Include deleted")

    def clean_purchase_date_end(self):
        validate_start_end_date_date(self.cleaned_data['purchase_date_start'],
                                     self.cleaned_data['purchase_date_end'])
        return self.cleaned_data['purchase_date_end']

    def clean_deprecation_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['deprecation_date_start'],
            self.cleaned_data['deprecation_date_end'])
        return self.cleaned_data['deprecation_date_end']

    def clean_warranty_expiration_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['warranty_expiration_date_start'],
            self.cleaned_data['warranty_expiration_date_end'])
        return self.cleaned_data['warranty_expiration_date_end']

    def clean_support_expiration_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['support_expiration_date_start'],
            self.cleaned_data['support_expiration_date_end'])
        return self.cleaned_data['support_expiration_date_end']

    def clean_address(self):
        data = self.cleaned_data['address']
        if data:
            if '/' in data:
                try:
                    ipaddr.IPNetwork(data)
                except ValueError:
                    raise forms.ValidationError("Invalid network")
            else:
                try:
                    ipaddr.IPv4Address(data)
                except ValueError:
                    raise forms.ValidationError("Invalid address")
        return data


class SearchFormWithAssets(SearchForm):
    without_asset = forms.BooleanField(
        required=False,
        label="Devices without linked asset",
    )
