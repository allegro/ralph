# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

from bob.forms import AutocompleteWidget
from django import forms
from lck.django.common.models import MACAddressField
from powerdns.models import Domain, Record

from ralph.discovery.models import Ethernet, IPAddress
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import (
    get_domain,
    get_revdns_records,
    is_valid_hostname,
)


def validate_domain_name(name):
    if not name:
        return
    if '*' not in name and not is_valid_hostname(name):
        raise forms.ValidationError("Invalid hostname")
    if not get_domain(name):
        raise forms.ValidationError("No such domain")
    return name.lower()


class DNSRecordForm(forms.ModelForm):
    ptr = forms.BooleanField(required=False)

    class Meta:
        model = Record
        fields = 'name', 'type', 'content', 'ptr'
        widgets = {
            'name': AutocompleteWidget(
                attrs={
                    'class': 'span12 dropdown',
                    'placeholder': "name",
                    'style': 'min-width: 16ex',
                },
            ),
            'content': AutocompleteWidget(
                attrs={
                    'class': 'span12 dropdown',
                    'placeholder': "content",
                    'style': 'min-width: 16ex',
                },
            ),
            'type': forms.Select(attrs={'class': 'span12'}),
        }

    def __init__(self, *args, **kwargs):
        self.hostnames = kwargs.pop('hostnames')
        self.ips = kwargs.pop('ips')
        limit_types = kwargs.pop('limit_types')
        super(DNSRecordForm, self).__init__(*args, **kwargs)
        self.is_extra = False
        self.fields['type'].choices = [(t, t) for t in limit_types]
        if self.instance.type in ('A', 'AAAA') and get_revdns_records(
                self.instance.content
        ).filter(
                content=self.instance.name
        ).exists():
            self.fields['ptr'].initial = True
        if not self.instance.name and self.hostnames:
            hostname = list(self.hostnames)[0]
            self.fields['name'].initial = hostname
            self.instance.name = hostname
        if not self.instance.type:
            self.fields['type'].initial = 'A'
            self.instance.type = 'A'
            self.is_extra = True
        self.fields['name'].widget.choices = [(n, n) for n in self.hostnames]
        self.fields['content'].widget.choices = [(ip, ip) for ip in self.ips]

    def clean_name(self):
        name = self.cleaned_data['name']
        return validate_domain_name(name)

    def clean_content(self):
        type = self.cleaned_data['type']
        content = self.cleaned_data['content']
        if type == 'CNAME':
            if content not in self.hostnames:
                raise forms.ValidationError(
                    "Invalid hostname for this device.")
            return validate_domain_name(content)
        elif type == 'A':
            try:
                address = ipaddr.IPAddress(content)
            except ValueError:
                raise forms.ValidationError("Invalid IP address")
            if self.is_extra:
                for r in Record.objects.filter(type='A', content=address):
                    raise forms.ValidationError(
                        "There is already an A DNS record for this IP "
                        "(%s)." % r.name
                    )
            return unicode(address)
        return content

    def clean_ptr(self):
        ptr = self.cleaned_data['ptr']
        type = self.cleaned_data['type']
        if ptr and type not in ('A', 'AAAA'):
            raise forms.ValidationError("Only A records can have PTR.")
        if self.instance:
            # Dirty hack, so that the formset has access to this.
            self.instance.ptr = ptr
        return ptr

    def clean(self):
        name = self.cleaned_data.get('name', '')
        type = self.cleaned_data.get('type', '')
        content = self.cleaned_data.get('content', '')
        ptr = self.cleaned_data.get('ptr', False)
        if not self.cleaned_data.get('id'):
            if Record.objects.filter(
                name=name,
                type=type,
                content=content,
            ).exists():
                raise forms.ValidationError(
                    "Record with name '{}', type '{}' and content '{}' already "  # noqa
                    "exists in the database.".format(name, type, content)
                )
        if type != 'CNAME' and name not in self.hostnames:
            self._errors.setdefault('name', []).append(
                "Invalid hostname for this device."
            )
        if ptr:
            domain_name = '%s.in-addr.arpa' % '.'.join(
                list(reversed(content.split('.')))[1:],
            )
            if not Domain.objects.filter(name=domain_name).exists():
                raise forms.ValidationError(
                    'Domain %s for %s PTR record not found.' % (
                        domain_name,
                        name,
                    ),
                )
        return self.cleaned_data


class DNSFormSetBase(forms.models.BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        self.hostnames = kwargs.pop('hostnames')
        self.limit_types = kwargs.pop('limit_types')
        self.ips = kwargs.pop('ips')
        super(DNSFormSetBase, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['hostnames'] = self.hostnames
        kwargs['limit_types'] = self.limit_types
        kwargs['ips'] = self.ips
        return super(DNSFormSetBase, self)._construct_form(i, **kwargs)

    def clean(self):
        if any(self.errors):
            return
        a_records_count = 0
        ptr_records_count = 0
        records = []
        for form in self.forms:
            cleaned_data = getattr(form, 'cleaned_data')
            if not cleaned_data:
                continue
            record = (
                cleaned_data.get('name'),
                cleaned_data.get('type'),
                cleaned_data.get('content'),
            )
            if record in records:
                raise forms.ValidationError(
                    "DNS form contains duplicated entries.",
                )
            else:
                records.append(record)
            if cleaned_data.get('type') == 'A':
                a_records_count += 1
                if cleaned_data.get('ptr', False):
                    ptr_records_count += 1
        if a_records_count > 0 and ptr_records_count == 0:
            raise forms.ValidationError(
                "Minimum one PTR record is required.",
            )


DNSFormSet = forms.models.modelformset_factory(
    Record,
    form=DNSRecordForm,
    formset=DNSFormSetBase,
    can_delete=True,
)


class DHCPEntryForm(forms.ModelForm):

    class Meta:
        model = DHCPEntry
        fields = 'ip', 'mac'
        widgets = {
            'ip': AutocompleteWidget(
                attrs={
                    'class': 'span12 dropdown',
                    'placeholder': "IP address",
                    'style': 'min-width: 16ex',
                },
            ),
            'mac': AutocompleteWidget(
                attrs={
                    'class': 'span12 dropdown',
                    'placeholder': "MAC address",
                    'style': 'min-width: 16ex',
                },
            ),
        }

    def clean_ip(self):
        ip = self.cleaned_data['ip']
        try:
            ip = unicode(ipaddr.IPAddress(ip))
        except ValueError:
            raise forms.ValidationError("Invalid IP address")
        return ip

    def clean_mac(self):
        mac = self.cleaned_data['mac']
        try:
            mac = MACAddressField.normalize(mac)
            if not mac:
                raise ValueError()
        except ValueError:
            raise forms.ValidationError("Invalid MAC address")
        return mac


class DHCPFormSetBase(forms.models.BaseModelFormSet):

    def __init__(self, records, macs, ips, device, *args, **kwargs):
        kwargs['queryset'] = records.all()
        self.records = list(records)
        self.macs = set(macs) - {r.mac for r in self.records}
        self.ips = set(ips) - {r.ip for r in self.records}
        self.device = device
        super(DHCPFormSetBase, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        form.fields['mac'].widget.choices = [(m, m) for m in self.macs]
        form.fields['ip'].widget.choices = [(ip, ip) for ip in self.ips]
        return super(DHCPFormSetBase, self).add_fields(form, index)

    def clean(self):
        if any(self.errors):
            return
        for form in self.forms:
            cleaned_data = getattr(form, 'cleaned_data')
            if not cleaned_data:
                continue
            mac_address = cleaned_data.get('mac')
            if Ethernet.objects.exclude(
                device=self.device,
            ).filter(
                mac=MACAddressField.normalize(mac_address),
            ).exists():
                raise forms.ValidationError(
                    "%s is assigned to another device." % mac_address,
                )


DHCPFormSet = forms.models.modelformset_factory(
    DHCPEntry,
    form=DHCPEntryForm,
    formset=DHCPFormSetBase,
    can_delete=True,
)


class IPAddressForm(forms.ModelForm):

    class Meta:
        model = IPAddress
        fields = 'hostname', 'address'
        widgets = {
            'hostname': forms.TextInput(
                attrs={
                    'class': 'span12',
                    'placeholder': "Hostname",
                    'style': 'min-width: 16ex',
                },
            ),
            'address': forms.TextInput(
                attrs={
                    'class': 'span12',
                    'placeholder': "IP address",
                    'style': 'min-width: 16ex',
                },
            ),
        }

    def clean_address(self):
        ip = self.cleaned_data['address']
        if not ip:
            return ''
        try:
            ip = unicode(ipaddr.IPAddress(ip))
        except ValueError:
            raise forms.ValidationError("Invalid IP address")
        return ip

    def clean_hostname(self):
        name = self.cleaned_data['hostname'].lower()
        if not name:
            return ''
        if not is_valid_hostname(name):
            raise forms.ValidationError("Invalid hostname")
        return name


IPAddressFormSet = forms.models.modelformset_factory(
    IPAddress,
    form=IPAddressForm,
    can_delete=True,
)
