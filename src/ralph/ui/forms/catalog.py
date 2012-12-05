# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal

from django import forms

from ralph.ui.widgets import CurrencyWidget
from ralph.discovery.models import ComponentModelGroup, DeviceModelGroup


class ModelGroupForm(forms.ModelForm):
    class Meta:
        exclude = ['type', 'last_seen', 'created', 'modified']

    icons = {
        'name': 'fugue-paper-bag',
        'price': 'fugue-money-coin',
        'per_size': 'fugue-ruler',
    }
    has_delete = True


class ComponentModelGroupForm(ModelGroupForm):
    class Meta(ModelGroupForm.Meta):
        model = ComponentModelGroup
        exclude = ModelGroupForm.Meta.exclude + [
                'price', 'size_modifier', 'size_unit', 'per_size']

    human_price = forms.DecimalField(label="Purchase price",
                                     widget=CurrencyWidget)
    human_unit = forms.ChoiceField(label="This price is for", choices=[
        ('piece', '1 piece'),
        ('core', '1 CPU core'),
        ('MiB', '1 MiB'),
        ('GiB', '1 GiB'),
        ('CPUh', '1 CPU hour'),
        ('GiBh', '1 GiB hour'),
    ])

    def __init__(self, *args, **kwargs):
        super(ComponentModelGroupForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.per_size:
                modifier = self.instance.size_modifier
                unit = self.instance.size_unit
                if unit == 'MiB' and modifier % 1024 == 0:
                    unit = 'GiB'
                    modifier = int(modifier/1024)
                price = decimal.Decimal(self.instance.price) / modifier
            else:
                price = self.instance.price
                unit = 'piece'
            self.fields['human_unit'].initial = unit
            self.fields['human_price'].initial = price

    def save(self, *args, **kwargs):
        unit =  self.cleaned_data['human_unit']
        price = self.cleaned_data['human_price']
        if unit == 'piece':
            self.instance.per_size = False
            self.instance.price = price
        else:
            self.instance.per_size = True
            if unit == 'GiB':
                modifier = 1024
                unit = 'MiB'
            else:
                modifier = 1
            while int(price) != price and modifier <= 100000000000:
                modifier *= 10
                price *= 10
            self.instance.size_modifier = modifier
            self.instance.price = int(price)
            self.instance.size_unit = unit
        return super(ComponentModelGroupForm, self).save(*args, **kwargs)


class DeviceModelGroupForm(ModelGroupForm):
    class Meta(ModelGroupForm.Meta):
        model = DeviceModelGroup


