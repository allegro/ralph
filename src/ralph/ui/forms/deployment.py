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
from powerdns.models import Record

from ralph.business.models import Venture, VentureRole
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
from ralph.dnsedit.util import is_valid_hostname, get_ip_addresses
from ralph.ui.widgets import DeviceWidget
from ralph.util import Eth
from ralph.util.csvutil import UnicodeReader


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
        macs = [e.mac for e in device.ethernet_set.order_by('mac')]
        self.fields['mac'].widget.choices = [(mac, mac) for mac in macs]
        # all mac addresses have the same length - default sorting is enough
        dhcp_entries = DHCPEntry.objects.filter(mac__in=macs).order_by('mac')
        ips = [e.ip for e in dhcp_entries]
        self.fields['ip'].widget.choices = [(ip, ip) for ip in ips]
        proposed_mac = macs[0] if macs else ''
        proposed_ip = ips[0] if ips else ''
        for dhcp_entry in dhcp_entries:
            if dhcp_entry.mac in macs:
                proposed_mac = dhcp_entry.mac
                proposed_ip = dhcp_entry.ip
                break
        self.initial.update({
            'mac': proposed_mac,
            'ip': proposed_ip,
            'venture': device.venture,
            'venture_role': device.venture_role,
            'preboot': (device.venture_role.get_preboot() if
                        device.venture_role else ''),
            'hostname': device.name,
        })
        self.fields['venture'].queryset = Venture.objects.order_by('name')

    def clean_hostname(self):
        hostname = self.cleaned_data['hostname'].strip().lower()
        if not is_valid_hostname(hostname):
            raise forms.ValidationError("Invalid hostname.")
        if '.' not in hostname:
            raise forms.ValidationError("Hostname has to include the domain.")
        return hostname

    def clean_ip(self):
        ip = self.cleaned_data.get('ip')
        return str(ipaddr.IPAddress(ip))


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


def _validate_management_ip(ip, row_number):
    try:
        ipaddr.IPAddress(ip)
    except ValueError:
        raise forms.ValidationError(
            "Row %s: Incorrect management IP address." % row_number
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
            "Row %d: Device with MAC %s exists and has child devices "
            "[%s]. Delete the child devices first." % (
                row_number,
                mac,
                ', '.join(str(d) for d in children.all()),
            )
        )
    if device.servermount_set.filter(device__deleted=False).exists():
        raise forms.ValidationError(
            "Row %d: Device with MAC %s exists and exports shares." %
            (row_number, mac)
        )
    for share in device.diskshare_set.all():
        if any((
            share.disksharemount_set.filter(device__deleted=False).exists(),
            share.disksharemount_set.filter(server__deleted=False).exists(),
        )):
            raise forms.ValidationError(
                "Row %d: Device with MAC %s exists and exports disks." %
                (row_number, mac)
            )


class PrepareMassDeploymentForm(forms.Form):
    csv = forms.CharField(
        label="CSV",
        widget=forms.widgets.Textarea(attrs={'class': 'span12 csv-input'}),
        required=False,
        help_text="Template: mac ; management-ip ; network ; venture-symbol ; "
                  "role ; preboot"
    )

    def clean_csv(self):
        csv_string = self.cleaned_data['csv'].strip().lower()
        rows = UnicodeReader(cStringIO.StringIO(csv_string))
        parsed_macs = set()
        for row_number, cols in enumerate(rows, start=1):
            _validate_cols_count(6, cols, row_number)
            mac = cols[0].strip()
            _validate_mac(mac, parsed_macs, row_number)
            _validate_deploy_children(mac, row_number)
            parsed_macs.add(mac)
            management_ip = cols[1].strip()
            _validate_management_ip(management_ip, row_number)
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


def _validate_hostname(hostname, mac, parsed_hostnames, row_number):
    mac = MACAddressField.normalize(mac)
    try:
        dev = Device.admin_objects.get(ethernet__mac=mac)
    except Device.DoesNotExist:
        if hostname_exists(hostname):
            raise forms.ValidationError(
                "Row %s: Hostname already exists." % row_number
            )
    else:
        ip_addresses = list(
            dev.ipaddress_set.values_list('address', flat=True)
        )
        ip_addresses_in_dns = get_ip_addresses(hostname)
        for ip in ip_addresses_in_dns:
            if ip not in ip_addresses:
                raise forms.ValidationError(
                    "Row %s: Using an old device %s failed. "
                    "Exists A or PTR records in DNS which are not assigned "
                    "to device IP addresses." % (row_number, dev)
                )
        if Deployment.objects.filter(hostname=hostname).exists():
            raise forms.ValidationError(
                "Row %s: Running deployment with hostname: %s already "
                "exists." % (row_number, hostname)
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


def _validate_ip_owner(ip, mac, row_number):
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
        # Does another device have this IPAddress?
        if(Device.objects.filter(
            ipaddress__number=int(ipaddr.IPAddress(ip)),
        ).exclude(
            pk=dev.id,
        ).exists()):
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
        parsed_hostnames = set()
        parsed_ip_addresses = set()
        parsed_macs = set()
        for row_number, cols in enumerate(rows, start=1):
            _validate_cols_count(9, cols, row_number)
            _validate_cols_not_empty(cols, row_number)
            mac = cols[3].strip()
            _validate_mac(mac, parsed_macs, row_number)
            parsed_macs.add(mac)
            hostname = cols[0].strip()
            _validate_hostname(hostname, mac, parsed_hostnames, row_number)
            parsed_hostnames.add(hostname)
            network_name = cols[5].strip()
            try:
                network = Network.objects.get(name=network_name)
            except Network.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Network '%s' doesn't exists." %
                    (row_number, network_name)
                )
            rack_sn = cols[2].strip()
            if re.match(r"^[0-9]+$", rack_sn):
                rack_sn = "Rack %s %s" % (
                    rack_sn,
                    network.data_center.name.upper(),
                )
            if not rack_exists(rack_sn):
                raise forms.ValidationError(
                    "Row %s: Rack with serial number '%s' doesn't exists." % (
                        row_number, rack_sn
                    )
                )
            try:
                network.racks.get(sn=rack_sn)
            except Device.DoesNotExist:
                raise forms.ValidationError(
                    "Row %s: Rack '%s' isn't connected to "
                    "network '%s'." % (row_number, rack_sn, network.name)
                )
            ip = cols[1].strip()
            _validate_ip_address(ip, network, parsed_ip_addresses, row_number)
            _validate_ip_owner(ip, mac, row_number)
            parsed_ip_addresses.add(ip)
            management_ip = cols[4].strip()
            _validate_management_ip(management_ip, row_number)
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

