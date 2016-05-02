# -*- coding: utf-8 -*-
from django import forms
from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.components import Ethernet
from ralph.networks.models import IPAddress


def validate_is_management(forms):
    """
    Validate is_management field in IpAddress formset
    """
    is_management = []
    for form in forms:
        cleaned_data = form.cleaned_data
        if (
            cleaned_data and
            not cleaned_data.get('DELETE', False)
        ):
            is_management.append(cleaned_data.get('is_management'))

    count_management_ip = is_management.count(True)
    if is_management and count_management_ip > 1:
        raise ValidationError((
            'Only one managment IP address can be assigned '
            'to this asset'
        ))


class SimpleNetworkForm(forms.ModelForm):
    hostname = forms.CharField(label='Hostname')
    address = forms.IPAddressField(label='IP address')
    is_management = forms.BooleanField(label='Is managment', required=False)

    ip_fields = ['hostname', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.ip = self.instance.ipaddress
        except AttributeError:
            self.ip = None
        else:
            for field in self.ip_fields:
                self.fields[field].initial = self.ip.__dict__[field]

    class Meta:
        model = Ethernet
        fields = [
            'hostname', 'address', 'mac',
        ]

    def clean_address(self):
        address = self.cleaned_data['address']
        qs = IPAddress.objects.filter(address=address)
        if self.ip:
            qs = qs.exclude(pk=self.ip.pk)
        if qs.exists():
            raise ValidationError(
                _('Address %(ip)s already exist.'),
                params={'ip': address},
            )
        return address

    def save(self, commit=True):
        obj = super().save(commit=True)
        ip_values = {
            key: value
            for key, value in self.cleaned_data.items()
            if key in self.ip_fields
        }
        if self.ip:
            self.ip.__dict__.update(ip_values)
        else:
            IPAddress.objects.create(ethernet=obj, **ip_values)
        return obj


class NetworkForm(SimpleNetworkForm):
    is_management = forms.BooleanField(label='Is managment', required=False)

    ip_fields = ['hostname', 'address', 'is_management']

    class Meta:
        model = Ethernet
        fields = [
            'hostname', 'address', 'mac', 'is_management', 'label', 'speed'
        ]


class NetworkInlineFormset(BaseInlineFormSet):

    def clean(self):
        validate_is_management(self.forms)
