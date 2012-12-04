# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal

from django import forms
from bob.forms import AutocompleteWidget

from ralph.deployment.models import Deployment
from ralph.business.models import RoleProperty
from ralph.discovery.models import (
    ComponentModelGroup,
    DeviceModelGroup,
    IPAddress,
)
from ralph.dnsedit.models import DHCPEntry
from ralph.ui.widgets import (
    DateWidget,
    CurrencyWidget,
    DeviceWidget,
)
from ralph.ui.forms.util import all_ventures


class DateRangeForm(forms.Form):
    start = forms.DateField(widget=DateWidget, label='Start date')
    end = forms.DateField(widget=DateWidget, label='End date')


class MarginsReportForm(DateRangeForm):
    margin_venture = forms.ChoiceField(choices=all_ventures())

    def __init__(self, margin_kinds, *args, **kwargs):
        super(MarginsReportForm, self).__init__(*args, **kwargs)
        for mk in margin_kinds:
            field_id = 'm_%d' % mk.id
            field = forms.IntegerField(label='', initial=mk.margin,
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'span12',
                        'style': 'text-align: right',
                    }))
            field.initial = mk.margin
            self.fields[field_id] = field

    def get(self, field, default=None):
        try:
            return self.cleaned_data[field]
        except (KeyError, AttributeError):
            try:
                return self.initial[field]
            except KeyError:
                return self.fields[field].initial




class VentureFilterForm(forms.Form):
    show_all = forms.BooleanField(required=False,
            label="Show all ventures")


class NetworksFilterForm(forms.Form):
    show_ip = forms.BooleanField(required=False,
            label="Show as addresses")
    contains = forms.CharField(required=False, label="Contains",
            widget=forms.TextInput(attrs={'class':'span12'}))


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


class DeploymentForm(forms.ModelForm):
    class Meta:
        model = Deployment
        fields = [
                'device',
                'venture',
                'venture_role',
                'mac',
                'ip',
                'hostname',
                'preboot',
            ]
        widgets = {
            'device': DeviceWidget,
            'mac': AutocompleteWidget,
            'ip': AutocompleteWidget,
        }

    def __init__(self, *args, **kwargs):
        super(DeploymentForm, self).__init__(*args, **kwargs)
        device = self.initial['device']
        macs = [e.mac for e in device.ethernet_set.all()]
        self.fields['mac'].widget.choices = [(mac, mac) for mac in macs]
        ips = [e.ip for e in DHCPEntry.objects.filter(mac__in=macs)]
        self.fields['ip'].widget.choices = [(ip, ip) for ip in ips]
        self.initial.update({
            'mac': macs[0] if macs else '',
            'ip': ips[0] if ips else '',
            'venture': device.venture,
            'venture_role': device.venture_role,
            'preboot': (device.venture_role.get_preboot() if
                        device.venture_role else ''),
            'hostname': device.name,
        })

    def clean_hostname(self):
        hostname = self.cleaned_data['hostname'].strip().lower()
        if not is_valid_hostname(hostname):
            raise forms.ValidationError("Invalid hostname.")
        if '.' not in hostname:
            raise forms.ValidationError("Hostname has to include the domain.")
        return hostname

    def clean_ip(self):
        ip = self.cleaned_data.get('ip')
        venture_role = self.cleaned_data.get('venture_role')
        if venture_role.check_ip(ip) is False:
            raise forms.ValidationError("Given IP isn't in the appropriate subnet")
        return ip

    def clean_device(self):
        device = self.cleaned_data['device']
        managements = self.device_management_count(device)
        if managements < 1:
            raise forms.ValidationError("doesn't have a management address")
        if managements > 1:
            raise forms.ValidationError("has more than one management address")
        return device

    def device_management_count(self, device):
        managements = IPAddress.objects.filter(device_id= device.id,
                                               is_management=True)
        return len(managements)


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


