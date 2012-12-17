# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
from bob.forms import AutocompleteWidget
from django import forms
from django.db.models import Q

from ralph.business.models import RoleProperty, VentureRole
from ralph.deployment.util import (
    is_mac_address_unknown, is_rack_exists, are_venture_and_role_exists,
    is_preboot_exists, is_hostname_exists, is_ip_address_exists,
    is_network_exists, is_management_ip_unique
)
from ralph.deployment.models import Deployment, Preboot
from ralph.discovery.models import Device, DeviceType, Network
from ralph.discovery.models_component import is_mac_valid
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import is_valid_hostname
from ralph.ui.forms.util import all_ventures
from ralph.ui.widgets import DateWidget, DeviceWidget
from ralph.util import Eth


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
        widget=forms.TextInput(attrs={'class':'span12'}),
    )


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


class PrepareMultipleDeploymentForm(forms.Form):
    csv = forms.CharField(
        label="CSV", widget=forms.widgets.Textarea(attrs={'class': 'span12'}),
        help_text="Template: mac;management-ip;network;venture;role;preboot"
    )

    def clean_csv(self):
        csv = self.cleaned_data['csv'].strip()
        rows = csv.split("\n")
        if not rows:
            raise forms.ValidationError("Incorrect CSV format.")
        parsed_macs = []
        parsed_management_ip_addresses = []
        for row_number, row in enumerate(rows, start=1):
            cols = row.split(";")
            if len(cols) != 6:
                raise forms.ValidationError(
                    "Incorrect CSV format. See row %s" % row_number
                )
            for col_number, col in enumerate(cols, start=1):
                value = col.strip()
                if not value:
                    raise forms.ValidationError(
                        "Incorrect CSV format. See row %s col %s" % (
                            row_number, col_number
                        )
                    )
            mac = cols[0].strip()
            if not is_mac_valid(Eth("", mac, "")):
                raise forms.ValidationError(
                    "Row %s: Invalid MAC address." % row_number
                )
            if not is_mac_address_unknown(mac):
                raise forms.ValidationError(
                    "Row %s: MAC address already exists." % row_number
                )
            if mac in parsed_macs:
                raise forms.ValidationError(
                    "Row %s: Duplicated MAC address. "
                    "Please check previous rows..." % row_number
                )
            parsed_macs.append(mac)
            management_ip = cols[1].strip()
            try:
                ipaddr.IPAddress(management_ip)
            except ValueError:
                raise forms.ValidationError(
                    "Row %s: Incorrect management IP address." % row_number
                )
            if not is_management_ip_unique(management_ip):
                raise forms.ValidationError(
                    "Row %s: Management IP address already exists." % (
                        row_number
                    )
                )
            if management_ip in parsed_management_ip_addresses:
                raise forms.ValidationError(
                    "Row %s: Duplicated management IP address. "
                    "Please check previous rows..." % row_number
                )
            parsed_management_ip_addresses.append(management_ip)
            network_name = cols[2].strip()
            if not is_network_exists(network_name):
                raise forms.ValidationError(
                    "Row %s: Network doesn't exists." % row_number
                )
            venture = cols[3].strip()
            venture_role = cols[4].strip()
            if not are_venture_and_role_exists(venture, venture_role):
                raise forms.ValidationError(
                    "Row %s: Couldn't find venture %s with role %s" % (
                        row_number, venture, venture_role
                    )
                )
            preboot = cols[5].strip()
            if not is_preboot_exists(preboot):
                raise forms.ValidationError(
                    "Row %s: Couldn't find preboot %s" % (
                        row_number, preboot
                    )
                )
        return csv


class MultipleDeploymentForm(forms.Form):
    csv = forms.CharField(
        label="CSV", widget=forms.widgets.Textarea(attrs={'class': 'span12'}),
        help_text="Template: hostname;ip;rack-sn;mac;management-ip;"
                  "network;venture;role;preboot"
    )

    def clean_csv(self):
        csv = self.cleaned_data['csv'].strip()
        rows = csv.split("\n")
        if not rows:
            raise forms.ValidationError("Incorrect CSV format.")
        cleaned_csv = []
        parsed_hostnames = []
        parsed_ip_addresses = []
        parsed_macs = []
        parsed_management_ip_addresses = []
        for row_number, row in enumerate(rows, start=1):
            cols = row.split(";")
            if len(cols) != 9:
                raise forms.ValidationError(
                    "Incorrect CSV format. See row %s" % row_number
                )
            for col_number, col in enumerate(cols, start=1):
                value = col.strip()
                if not value:
                    raise forms.ValidationError(
                        "Incorrect CSV format. See row %s col %s" % (
                            row_number, col_number
                        )
                    )
            hostname = cols[0].strip()
            if is_hostname_exists(hostname):
                raise forms.ValidationError(
                    "Row %s: Hostname already exists." % row_number
                )
            if hostname in parsed_hostnames:
                raise forms.ValidationError(
                    "Row %s: Duplicated hostname. "
                    "Please check previous rows..." % row_number
                )
            parsed_hostnames.append(hostname)
            rack_sn = cols[2].strip()
            try:
                Device.objects.get(
                    Q(sn=rack_sn),
                    Q(model__type=DeviceType.rack) |
                    Q(model__type=DeviceType.blade_system)
                )
            except Device.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Rack with SN=%s doesn't exists." % (
                        row_number, rack_sn
                    )
                )
            network_name = cols[5].strip()
            try:
                network = Network.objects.get(name=network_name)
            except Network.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Selected network doesn't exists." % row_number
                )
            if rack_sn not in network.rack:
                raise forms.ValidationError(
                    "Row %s: Selected rack isn't connected with selected "
                    "network" % row_number
                )
            ip = cols[1].strip()
            try:
                ip_number = int(ipaddr.IPAddress(ip))
                if ip_number < network.min_ip or ip_number > network.max_ip:
                    raise forms.ValidationError(
                        "Row %s: IP address is not valid for network %s." % (
                            row_number, network.name
                        )
                    )
            except ValueError:
                raise forms.ValidationError(
                    "Row %s: Invalid IP address." % row_number
                )
            if is_ip_address_exists(ip):
                raise forms.ValidationError(
                    "Row %s: IP address already exists." % row_number
                )
            if ip in parsed_ip_addresses:
                raise forms.ValidationError(
                    "Row %s: Duplicated IP address. "
                    "Please check previous rows..." % row_number
                )
            parsed_ip_addresses.append(ip)
            mac = cols[3].strip()
            if not is_mac_valid(Eth("", mac, "")):
                raise forms.ValidationError(
                    "Row %s: Invalid MAC address." % row_number
                )
            if not is_mac_address_unknown(mac):
                raise forms.ValidationError(
                    "Row %s: MAC address already exists." % row_number
                )
            if mac in parsed_macs:
                raise forms.ValidationError(
                    "Row %s: Duplicated MAC address. "
                    "Please check previous rows..." % row_number
                )
            parsed_macs.append(mac)
            management_ip = cols[4].strip()
            try:
                ipaddr.IPAddress(management_ip)
            except ValueError:
                raise forms.ValidationError(
                    "Row %s: Invalid management IP address." % row_number
                )
            if not is_management_ip_unique(management_ip):
                raise forms.ValidationError(
                    "Row %s: Management IP address already exists." % (
                        row_number
                    )
                )
            if management_ip in parsed_management_ip_addresses:
                raise forms.ValidationError(
                    "Row %s: Duplicated management IP address. "
                    "Please check previous rows..." % row_number
                )
            parsed_management_ip_addresses.append(management_ip)
            try:
                venture_role = VentureRole.objects.get(
                    venture__name=cols[6].strip(),
                    name=cols[7].strip()
                )
                venture = venture_role.venture
            except VentureRole.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Couldn't find venture %s with role %s" % (
                        row_number, cols[6].strip(), cols[7].strip()
                    )
                )
            try:
                preboot = Preboot.objects.get(name=cols[8].strip())
            except Preboot.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Couldn't find preboot %s" % (
                        row_number, cols[8].strip()
                    )
                )
            cleaned_csv.append({
                'hostname': hostname,
                'ip': ip,
                'mac': mac,
                'rack_sn': rack_sn,
                'venture': venture,
                'venture_role': venture_role,
                'preboot': preboot,
                'management_ip': management_ip,
                'network': network
            })
        return cleaned_csv


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

