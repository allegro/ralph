# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.discovery.models import Network, NetworkKind


class NetworksFilterForm(forms.Form):
    contains = forms.CharField(
        required=False, label="Contains",
        widget=forms.TextInput(attrs={'class': 'span12'}),
    )
    kind = forms.ChoiceField(
        required=False,
        label="Network Kind",
        choices=[("", "")] + [
            (nk.id, nk.name) for nk in NetworkKind.objects.all()
        ],
        widget=forms.Select(
            attrs={'class': 'span12'},
        ),
    )


class NetworkForm(forms.ModelForm):

    class Meta:
        model = Network
        exclude = [
            'created',
            'modified',
            'min_ip',
            'max_ip',
            'last_scan',
        ]

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if not re.search(r'/[0-9]{1,2}$', address):
            raise forms.ValidationError(_("It's not a valid network address."))
        try:
            net = ipaddr.IPNetwork(address)
        except ValueError:
            raise forms.ValidationError(_("It's not a valid network address."))
        given_network_addr = net.compressed.split('/', 1)[0]
        real_network_addr = net.network.compressed
        if given_network_addr != real_network_addr:
            msg = "{} is invalid network address, valid network is {}".format(
                given_network_addr,
                real_network_addr,
            )
            raise forms.ValidationError(msg)
        return address

    def clean(self):
        cleaned_data = super(NetworkForm, self).clean()
        if cleaned_data.get('dhcp_broadcast', False):
            if not cleaned_data.get('gateway'):
                raise forms.ValidationError(_(
                    "To broadcast this network in DHCP config you must also "
                    "complete the `Gateway` field.",
                ))
        return cleaned_data
