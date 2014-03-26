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
from django.forms import formsets
from django.db.models import Q
from lck.django.common.models import MACAddressField
from powerdns.models import Record, Domain

from ralph.business.models import Venture, VentureRole
from ralph.deployment.models import Deployment, Preboot
from ralph.deployment.util import (
    clean_hostname,
    hostname_exists,
    ip_address_exists,
    is_mac_address_known,
    network_exists,
    preboot_exists,
    rack_exists,
    venture_and_role_exists,
)
from ralph.discovery.models import Device, Network, IPAddress, DeviceType
from ralph.discovery.models_component import is_mac_valid
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import (
    find_addresses_for_hostname,
    get_domain,
    get_revdns_records,
    is_valid_hostname,
)
from ralph.ui.widgets import DeviceWidget
from ralph.util import Eth
from bob.csvutil import UnicodeReader
from ralph.ui.widgets import ReadOnlySelectWidget, ReadOnlyWidget


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
        hostname = self.cleaned_data['hostname']
        return clean_hostname(hostname)

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
        ip_addresses_in_dns = find_addresses_for_hostname(hostname)
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
            if not clean_hostname(hostname):
                raise forms.ValidationError("Invalid hostname")

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


class ServerMoveStep1Form(forms.Form):
    addresses = forms.CharField(
        label="Server addresses",
        widget=forms.widgets.Textarea(attrs={'class': 'span12'}),
        help_text="Enter the IP addresses or hostnames to be moved, "
                  "separated with spaces or newlines.",
    )

    @staticmethod
    def _get_address_candidates(address):
        try:
            ip_address = str(ipaddr.IPAddress(address))
        except ValueError:
            ip_address = None
            try:
                mac = MACAddressField.normalize(address)
            except ValueError:
                mac = None
            if not mac:
                hostname = address
        if ip_address:
            candidates = IPAddress.objects.filter(
                address=ip_address,
            )
        elif mac:
            ips = {
                str(ip) for ip in
                DHCPEntry.objects.filter(mac=mac).values_list('ip', flat=True)
            }
            candidates = IPAddress.objects.filter(address__in=ips)
        else:
            candidates = IPAddress.objects.filter(
                Q(hostname=hostname) |
                Q(address__in=find_addresses_for_hostname(hostname))
            )
        return candidates.filter(
            device__deleted=False,
            device__model__type__in={
                DeviceType.rack_server,
                DeviceType.blade_server,
                DeviceType.virtual_server,
                DeviceType.unknown,
            }
        )

    def clean_addresses(self):
        addresses = self.cleaned_data['addresses']
        for address in addresses.split():
            if not self._get_address_candidates(address).exists():
                raise forms.ValidationError(
                    "No server found for %s." % address,
                )
        return addresses


def _check_move_address(address):
    if not IPAddress.objects.filter(
            device__deleted=False,
            device__model__type__in={
                DeviceType.rack_server,
                DeviceType.blade_server,
                DeviceType.virtual_server,
                DeviceType.unknown,
            }
    ).filter(address=address).exists():
        raise forms.ValidationError(
            "No server found for %s." % address,
        )


class ServerMoveStep2Form(forms.Form):
    address = forms.ChoiceField()
    network = forms.ChoiceField()

    def clean_address(self):
        address = self.cleaned_data['address']
        _check_move_address(address)
        return address

    def clean_network(self):
        network_id = self.cleaned_data['network']
        if not Network.objects.filter(id=network_id).exists():
            raise forms.ValidationError("Invalid network.")
        return network_id


class ServerMoveStep2FormSetBase(formsets.BaseFormSet):

    def add_fields(self, form, index):
        form.fields['network'].choices = [
            (n.id, n.name)
            for n in Network.objects.order_by('name')
        ]
        form.fields['network'].widget.attrs = {
            'class': 'span12',
        }
        if self.initial:
            candidates = self.initial[index]['candidates']
        else:
            candidates = {form.data['%s-%d-address' % (self.prefix, index)]}
        form.fields['address'].widget.attrs = {
            'class': 'span12',
        }
        if len(candidates) == 1:
            form.fields['address'].widget = ReadOnlySelectWidget()
        form.fields['address'].choices = [(ip, ip) for ip in candidates]
        return super(ServerMoveStep2FormSetBase, self).add_fields(form, index)


ServerMoveStep2FormSet = formsets.formset_factory(
    form=ServerMoveStep2Form,
    formset=ServerMoveStep2FormSetBase,
    extra=0,
)


class ServerMoveStep3Form(forms.Form):
    address = forms.CharField(widget=ReadOnlyWidget())
    new_ip = forms.CharField()
    new_hostname = forms.CharField()

    def clean_address(self):
        address = self.cleaned_data['address']
        _check_move_address(address)
        return address

    def clean_new_ip(self):
        old_ip = self.cleaned_data.get('address')
        new_ip = self.cleaned_data['new_ip']
        try:
            new_ip = str(ipaddr.IPAddress(new_ip))
        except ValueError:
            raise forms.ValidationError("Malformed IP address.")
        rdomain = '.'.join(
            list(reversed(new_ip.split('.')))[1:]
        ) + '.in-addr.arpa'
        if not Domain.objects.filter(name=rdomain).exists():
            raise forms.ValidationError("No RevDNS domain for address.")
        try:
            ipaddress = IPAddress.objects.get(address=new_ip)
        except IPAddress.DoesNotExist:
            if Record.objects.filter(content=new_ip).exists():
                raise forms.ValidationError("Address already in DNS.")
            if get_revdns_records(new_ip).exists():
                raise forms.ValidationError("Address already in DNS.")
            if DHCPEntry.objects.filter(ip=new_ip).exists():
                raise forms.ValidationError("Address already in DHCP.")
        else:
            if ipaddress.device and not ipaddress.device.deleted:
                if not old_ip:
                    raise forms.ValidationError("Address in use.")
                device = Device.objects.get(ipaddress__address=old_ip)
                if ipaddress.device.id != device.id:
                    raise forms.ValidationError(
                        "Address used by %s" % device,
                    )
        return new_ip

    def clean_new_hostname(self):
        old_ip = self.cleaned_data.get('address')
        new_hostname = self.cleaned_data['new_hostname']
        if not is_valid_hostname(new_hostname):
            raise forms.ValidationError("Invalid hostname")
        try:
            get_domain(new_hostname)
        except Domain.DoesNotExist:
            raise forms.ValidationError("Invalid domain")
        try:
            ipaddress = IPAddress.objects.get(hostname=new_hostname)
        except IPAddress.DoesNotExist:
            if find_addresses_for_hostname(new_hostname):
                raise forms.ValidationError("Hostname already in DNS.")
        else:
            if ipaddress.device and not ipaddress.device.deleted:
                if not old_ip:
                    raise forms.ValidationError("Hostname in use.")
                device = Device.objects.get(ipaddress__address=old_ip)
                if ipaddress.device.id != device.id:
                    raise forms.ValidationError(
                        "Hostname used by %s" % device,
                    )
            elif Record.objects.filter(name=new_hostname).exists():
                raise forms.ValidationError("Hostname already in DNS.")
        return new_hostname


class ServerMoveStep3FormSetBase(formsets.BaseFormSet):

    def clean(self):
        if any(self.errors):
            return
        hostnames = set()
        ips = set()
        for i in xrange(self.total_form_count()):
            form = self.forms[i]
            ip = form.cleaned_data['new_ip']
            if ip in ips:
                form._errors['new_ip'] = form.error_class([
                    "Duplicate IP"
                ])
            else:
                ips.add(ip)
            hostname = form.cleaned_data['new_hostname']
            if hostname in hostnames:
                form._errors['new_hostname'] = form.error_class([
                    "Duplicate hostname"
                ])
            else:
                hostnames.add(hostname)


ServerMoveStep3FormSet = formsets.formset_factory(
    form=ServerMoveStep3Form,
    formset=ServerMoveStep3FormSetBase,
    extra=0,
)
