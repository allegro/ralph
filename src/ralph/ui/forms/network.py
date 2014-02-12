# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms

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
