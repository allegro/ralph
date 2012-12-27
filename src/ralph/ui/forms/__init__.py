# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import cStringIO
import re

import ipaddr
from bob.forms import AutocompleteWidget
from django import forms
from lck.django.common.models import MACAddressField

from ralph.business.models import RoleProperty, VentureRole
from ralph.deployment.models import Deployment, Preboot
from ralph.deployment.util import (
    hostname_exists,
    ip_address_exists,
    is_mac_address_known,
    network_exists,
    preboot_exists,
    rack_exists,
    venture_and_role_exists,
)
from ralph.discovery.models import Device, Network
from ralph.discovery.models_component import is_mac_valid
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import is_valid_hostname
from ralph.ui.forms.util import all_ventures
from ralph.ui.widgets import DateWidget, DeviceWidget
from ralph.util import Eth
from ralph.util.csvutil import UnicodeReader



class DateRangeForm(forms.Form):
    start = forms.DateField(widget=DateWidget, label='Start date')
    end = forms.DateField(widget=DateWidget, label='End date')


class MarginsReportForm(DateRangeForm):
    margin_venture = forms.ChoiceField(choices=all_ventures())

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
            raise forms.ValidationError(
                "Given IP isn't in the appropriate subnet"
            )
        return ip


def _validate_cols_count(expected_count, cols, row_number):
    if len(cols) != expected_count:
        raise forms.ValidationError(
            "Incorrect number of columns (got %d, expected %d) at row %d" %
            (len(cols), expected_count, row_number),
        )


def _validate_cols_not_empty(cols, row_number):
    for col_number, col in enumerate(cols, start=1):
        value = col.strip()
        if not value:
            raise forms.ValidationError(
                "Empty value at row %d column %d" % (
                    row_number, col_number
                )
            )


def _validate_mac(mac, parsed_macs, row_number):
    if not is_mac_valid(Eth("", mac, "")):
        raise forms.ValidationError(
            "Row %s: Invalid MAC address." % row_number
        )
    if mac in parsed_macs:
        raise forms.ValidationError(
            "Row %s: Duplicated MAC address. "
            "Please check previous rows..." % row_number
        )


def _validate_management_ip(ip, parsed_management_ip_addresses, row_number):
    try:
        ipaddr.IPAddress(ip)
    except ValueError:
        raise forms.ValidationError(
            "Row %s: Incorrect management IP address." % row_number
        )
    if ip in parsed_management_ip_addresses:
        raise forms.ValidationError(
            "Row %s: Duplicated management IP address. "
            "Please check previous rows..." % row_number
        )


def _validate_network_name(network_name, row_number):
    if not network_exists(network_name):
        raise forms.ValidationError(
            "Row %s: Network doesn't exists." % row_number
        )


def _validate_venture_and_role(venture_symbol, venture_role, row_number):
    if not venture_and_role_exists(venture_symbol, venture_role):
        raise forms.ValidationError(
            "Row %s: "
            "Couldn't find venture with symbol %s and role %s" % (
                row_number, venture_symbol, venture_role
            )
        )


def _validate_preboot(preboot, row_number):
    if not preboot_exists(preboot):
        raise forms.ValidationError(
            "Row %s: Couldn't find preboot %s" % (
                row_number, preboot
            )
        )


def _validate_deploy_children(mac, row_number):
    mac = MACAddressField.normalize(mac)
    try:
        device = Device.admin_objects.get(ethernet__mac=mac)
    except Device.DoesNotExist:
        return
    if device.deleted:
        return
    children = device.child_set.filter(deleted=False)
    if children.exists():
        raise forms.ValidationError(
            "Row %d: Device with mac %s exists and has child devices "
            "[%s]." % (row_number, mac, ', '.join(children.all()))
        )
    if device.servermount_set.filter(device__deleted=False).exists():
        raise forms.ValidationError(
            "Row %d: Device with mac %s exists and exports shares" %
            (row_number, mac)
        )
    for share in device.diskshare_set.all():
        if any((
            share.disksharemount_set.filter(device__deleted=False).exists(),
            share.disksharemount_set.filter(server__deleted=False).exists(),
        )):
            raise forms.ValidationError(
                "Row %d: Device with mac %s exists and exports disks" %
                (row_number, mac)
            )


class PrepareMassDeploymentForm(forms.Form):
    csv = forms.CharField(
        label="CSV",
        widget=forms.widgets.Textarea(attrs={'class': 'span12 csv-input'}),
        help_text="Template: mac ; management-ip ; network ; venture-symbol ; "
                  "role ; preboot"
    )

    def clean_csv(self):
        csv_string = self.cleaned_data['csv'].strip().lower()
        rows = UnicodeReader(cStringIO.StringIO(csv_string))
        parsed_macs = []
        parsed_management_ip_addresses = []
        for row_number, cols in enumerate(rows, start=1):
            _validate_cols_count(6, cols, row_number)
            mac = cols[0].strip()
            _validate_mac(mac, parsed_macs, row_number)
            _validate_deploy_children(mac, row_number)
            parsed_macs.append(mac)
            management_ip = cols[1].strip()
            _validate_management_ip(
                management_ip, parsed_management_ip_addresses, row_number,
            )
            parsed_management_ip_addresses.append(management_ip)
            network_name = cols[2].strip()
            if not (is_mac_address_known(mac) and network_name == ''):
                # Allow empty network when the device already exists.
                _validate_network_name(network_name, row_number)
            venture_symbol = cols[3].strip()
            venture_role = cols[4].strip()
            _validate_venture_and_role(
                venture_symbol, venture_role, row_number,
            )
            preboot = cols[5].strip()
            _validate_preboot(preboot, row_number)
        return csv_string


def _validate_hostname(hostname, parsed_hostnames, row_number):
    if hostname_exists(hostname):
        raise forms.ValidationError(
            "Row %s: Hostname already exists." % row_number
        )
    if hostname in parsed_hostnames:
        raise forms.ValidationError(
            "Row %s: Duplicated hostname. "
            "Please check previous rows..." % row_number
        )


def _validate_ip_address(ip, network, parsed_ip_addresses, row_number):
    try:
        ipaddr.IPAddress(ip)
    except ValueError:
        raise forms.ValidationError(
            "Row %s: Invalid IP address." % row_number
        )
    if ip not in network:
        raise forms.ValidationError(
            "Row %s: IP address is not valid for network %s." % (
                row_number, network.name
            )
        )
    if ip in parsed_ip_addresses:
        raise forms.ValidationError(
            "Row %s: Duplicated IP address. "
            "Please check previous rows..." % row_number
        )

def _validate_ip_owner(ip, mac):
    """If the MAC is unique, make sure the IP address is not used anywhere.
    If the MAC address belongs to an existing device, make sure the IP address
    also belongs to that device.
    """
    mac = MACAddressField.normalize(mac)
    try:
        dev = Device.admin_objects.get(ethernet__mac=mac)
    except Device.DoesNotExist:
        if ip_address_exists(ip):
            raise forms.ValidationError(
                "Row %s: IP address already exists." % row_number
            )
    else:
        if not dev.ipaddress_set.filter(
            number=int(ipaddr.IPAddress(ip))
        ).exists():
            raise forms.ValidationError(
                "Row %s: IP address used by another device." % row_number
            )


class MassDeploymentForm(forms.Form):
    csv = forms.CharField(
        label="CSV",
        widget=forms.widgets.Textarea(attrs={'class': 'span12 csv-input'}),
        help_text="Template: hostname ; ip ; rack-sn ; mac ; management-ip ; "
                  "network ; venture-symbol ; role ; preboot"
    )

    def clean_csv(self):
        csv_string = self.cleaned_data['csv'].strip().lower()
        rows = UnicodeReader(cStringIO.StringIO(csv_string))
        cleaned_csv = []
        parsed_hostnames = []
        parsed_ip_addresses = []
        parsed_macs = []
        parsed_management_ip_addresses = []
        for row_number, cols in enumerate(rows, start=1):
            _validate_cols_count(9, cols, row_number)
            _validate_cols_not_empty(cols, row_number)
            hostname = cols[0].strip()
            _validate_hostname(hostname, parsed_hostnames, row_number)
            parsed_hostnames.append(hostname)
            rack_sn = cols[2].strip()
            if re.match(r"^[0-9]+$", rack_sn):
                rack_sn = "rack %s" % rack_sn
            if not rack_exists(rack_sn):
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
            try:
                network.racks.get(sn=rack_sn)
            except Device.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Selected rack isn't connected with selected "
                    "network" % row_number
                )
            ip = cols[1].strip()
            mac = cols[3].strip()
            _validate_ip_address(ip, network, parsed_ip_addresses, row_number)
            _validate_ip_owner(ip, mac)
            parsed_ip_addresses.append(ip)
            _validate_mac(mac, parsed_macs, row_number)
            parsed_macs.append(mac)
            management_ip = cols[4].strip()
            _validate_management_ip(
                management_ip, parsed_management_ip_addresses, row_number,
            )
            parsed_management_ip_addresses.append(management_ip)
            try:
                venture_role = VentureRole.objects.get(
                    venture__symbol=cols[6].strip().upper(),
                    name=cols[7].strip()
                )
                venture = venture_role.venture
            except VentureRole.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: "
                    "Couldn't find venture with symbol %s and role %s" % (
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


