# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal
import ipaddr

from django import forms
from lck.django.choices import Choices
from lck.django.common.models import MACAddressField
from bob.forms import AutocompleteWidget
from powerdns.models import Record

from ralph.business.models import Venture, RoleProperty, VentureRole
from ralph.deployment.models import Deployment
from ralph.discovery.models_component import is_mac_valid

from ralph.discovery.models import (Device, ComponentModelGroup,
                                    DeviceModelGroup, DeviceType, IPAddress)
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import is_valid_hostname, get_domain, get_revdns_records
from ralph.util import Eth
from ralph.ui.widgets import (DateWidget, CurrencyWidget,
                              ReadOnlySelectWidget, DeviceGroupWidget,
                              ComponentGroupWidget, DeviceWidget,
                              DeviceModelWidget, ReadOnlyWidget, RackWidget,
                              ReadOnlyPriceWidget)


def _all_ventures():
    yield '', '---------'
    for v in Venture.objects.filter(
                show_in_ralph=True,
            ).order_by(
                '-is_infrastructure', 'path'
            ):
        yield v.id, '\u00A0' * 4 * v.path.count('/') + v.name


def _all_roles():
    yield '', '---------'
    for r in VentureRole.objects.order_by(
                '-venture__is_infrastructure', 'venture__name',
                'parent__parent__name', 'parent__name', 'name'
            ):
        yield r.id, '{} / {}'.format(r.venture.name, r.full_name)


def validate_start_end_date_date(start, end):
    if start and end and start > end:
        raise forms.ValidationError(
                "The end date has to be later than the start date")


class TooltipContent(Choices):
    _ = Choices.Choice

    empty_field = _('Enter "none" to search for empty fields')
    empty_field_venture = _('Enter "none" or "-" to search for empty fields')


class DateRangeForm(forms.Form):
    start = forms.DateField(widget=DateWidget, label='Start date')
    end = forms.DateField(widget=DateWidget, label='End date')


class MarginsReportForm(DateRangeForm):
    margin_venture = forms.ChoiceField(choices=_all_ventures())

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

def _dns_char_field(label=None, initial=None, record=None, **kwargs):
    kwargs.update(
        label=label,
        initial=initial,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'span12',
            'placeholder': label,
            'style': 'min-width: 16ex',
        })
    )
    return forms.CharField(**kwargs)


def _dns_int_field(label=None, initial=None, **kwargs):
    kwargs.update(
        label=label,
        initial=initial,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'span12',
            'placeholder': label,
        })
    )
    return forms.IntegerField(**kwargs)





def _dns_type_field(label=None, initial=None, types=None, **kwargs):
    if types is None:
        types = list(Record.RECORD_TYPE)
        types.insert(0, ('', ''))
    return forms.ChoiceField(
        label=label,
        choices=types,
        initial=initial,
        widget=forms.Select(attrs={'class':'span12'}),
        required=False,
        **kwargs
    )


def _dns_type_limited_field(label=None, initial=None, **kwargs):
    kwargs.update(types=[('A', 'A'), ('CNAME', 'CNAME'), ('MX', 'MX'),
                         ('TXT', 'TXT')])
    return _dns_type_field(label, initial, **kwargs)


def _bool_field(label=None, initial=None, **kwargs):
    return forms.BooleanField(label=label, required=False, **kwargs)


def _bool_hidden_field(label=None, initial=None, **kwargs):
    kwargs.update(widget=forms.HiddenInput())
    return forms.BooleanField(label=label, required=False, **kwargs)


def validate_mac(mac):
    if not mac:
        return
    try:
        mac = MACAddressField.normalize(mac)
        if not mac:
            raise ValueError()
    except ValueError:
        raise forms.ValidationError("Invalid MAC address")
    return mac


def validate_ip(ip):
    if not ip:
        return
    try:
        address = ipaddr.IPAddress(ip)
    except ValueError:
        raise forms.ValidationError("Invalid IP address")
    return str(address)

def validate_domain_name(name):
    if not name:
        return
    if '*' not in name and not is_valid_hostname(name):
        raise forms.ValidationError("Invalid hostname")
    if not get_domain(name):
        raise forms.ValidationError("No such domain")
    return name.lower()

def _dhcp_mac_field(label=None, initial=None, record=None, **kwargs):
    kwargs.update(validators=[validate_mac])
    return _dns_char_field(label, initial, **kwargs)

def _ip_name_field(label=None, initial=None, record=None, **kwargs):
    kwargs.update(validators=[validate_domain_name])
    return _dns_char_field(label, initial, **kwargs)

def _dhcp_ip_field(label=None, initial=None, record=None, **kwargs):
    kwargs.update(validators=[validate_ip])
    return _dns_char_field(label, initial, **kwargs)


def _add_fields(new_fields, prefix, record, fields):
    for label, field_class in fields:
        initial = getattr(record, label, None)
        field = field_class(label, initial)
        field.initial = initial
        field.record = record
        field_id = prefix + label
        new_fields[field_id] = field


class DNSRecordsForm(forms.Form):
    def __init__(self, records, hostnames, *args, **kwargs):
        super(DNSRecordsForm, self).__init__(*args, **kwargs)
        self.records = list(records)
        self.hostnames = hostnames
        def _dns_name_field(label=None, initial=None, **kwargs):
            kwargs.update(
                label=label,
                initial=initial,
                required=False,
                validators=[validate_domain_name],
                widget=AutocompleteWidget(
                    attrs={
                        'class': 'span12',
                        'placeholder': label,
                        'style': 'min-width: 16ex',
                    },
                    choices=[(n, n) for n in hostnames],
                ),
            )
            return forms.CharField(**kwargs)
        fields = [
            ('name', _dns_name_field),
            ('type', _dns_type_limited_field),
            ('content', _dns_char_field),
            ('ptr', _bool_field),
            ('del', _bool_field),
        ]
        for record in self.records:
            if record.type in ('A', 'AAAA'):
                record.ptr = False
                for r in get_revdns_records(
                    record.content
                ).filter(content=record.name):
                    record.ptr = True
            prefix = 'dns_%d_' % record.id
            _add_fields(self.fields, prefix, record, fields)
        fields = [
            ('name', _dns_name_field),
            ('type', _dns_type_limited_field),
            ('content', _dns_char_field),
            ('ptr', _bool_field),
            ('del', _bool_hidden_field),
        ]
        _add_fields(self.fields, 'dns_new_', None, fields)
        if hostnames:
            self.fields['dns_new_name'].initial = list(hostnames)[0]

    def clean_dns_new_content(self):
        name = self.cleaned_data.get('dns_new_name', '')
        type = self.cleaned_data.get('dns_new_type', '')
        content = self.cleaned_data.get('dns_new_content', '')
        if Record.objects.filter(name=name, type=type,
                                 content=content).exists():
            raise forms.ValidationError("This DNS record already exists.")
        return content or ''

    def clean(self):
        for field_name, field in self.fields.iteritems():
            if field_name.endswith('_name'):
                name = self.cleaned_data.get(field_name, '')
                type = self.cleaned_data.get(
                    field_name.replace('_name', '_type')
                )
                content = self.cleaned_data.get(
                    field_name.replace('_name', '_content')
                )
                if not content and field_name.startswith('dns_new_'):
                    continue
                if type != 'CNAME' and name not in self.hostnames:
                    self._errors.setdefault(field_name, []).append(
                        "Invalid hostname for this device."
                    )
            elif field_name.endswith('_content'):
                content = self.cleaned_data.get(field_name, '')
                type = self.cleaned_data.get(
                    field_name.replace('_content', '_type')
                )
                if not content and not field_name.startswith('dns_new_'):
                    self._errors.setdefault(field_name, []).append(
                        "Content cannot be empty."
                    )
                if type == 'CNAME' and content not in self.hostnames:
                    self._errors.setdefault(field_name, []).append(
                        "Invalid hostname for this device."
                    )
                if type == 'A':
                    try:
                        ip = str(validate_ip(content))
                    except forms.ValidationError as e:
                        self._errors.setdefault(field_name, []).append(
                            "Invalid IP address."
                        )
                    if field_name.startswith('dns_new_'):
                        for r in Record.objects.filter(type='A', content=ip):
                            self._errors.setdefault(field_name, []).append(
                                "There is already an A DNS record for this IP "
                                "(%s)." % r.name
                            )
        return self.cleaned_data



class DHCPRecordsForm(forms.Form):
    def __init__(self, records, *args, **kwargs):
        super(DHCPRecordsForm, self).__init__(*args, **kwargs)
        self.records = list(records)
        fields = [
            ('ip', _dhcp_ip_field),
            ('mac', _dhcp_mac_field),
            ('del', _bool_field),
        ]
        for record in self.records:
            prefix = 'dhcp_%d_' % record.id
            _add_fields(self.fields, prefix, record, fields)
        fields = [
            ('ip', _dhcp_ip_field),
            ('mac', _dhcp_mac_field),
            ('del', _bool_hidden_field),
        ]
        _add_fields(self.fields, 'dhcp_new_', None, fields)


class AddressesForm(forms.Form):
    def __init__(self, records, *args, **kwargs):
        super(AddressesForm, self).__init__(*args, **kwargs)
        self.records = list(records)
        fields = [
            ('hostname', _ip_name_field),
            ('address', _dhcp_ip_field),
            ('del', _bool_field),
        ]
        for record in self.records:
            prefix = 'ip_%d_' % record.id
            _add_fields(self.fields, prefix, record, fields)
        fields = [
            ('hostname', _ip_name_field),
            ('address', _dhcp_ip_field),
            ('del', _bool_hidden_field),
        ]
        _add_fields(self.fields, 'ip_new_', None, fields)


class VentureFilterForm(forms.Form):
    show_all = forms.BooleanField(required=False,
            label="Show all ventures")


class NetworksFilterForm(forms.Form):
    show_ip = forms.BooleanField(required=False,
            label="Show as addresses")
    contains = forms.CharField(required=False, label="Contains",
            widget=forms.TextInput(attrs={'class':'span12'}))


class SearchForm(forms.Form):
    name = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span12'}))
    address = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field,
            }),
            label="Address or network")
    remarks = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field
            }))
    role = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field,
            }),
            label="Venture or role")
    model = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field_venture,
            }))
    component = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span12'}),
            label="Component or software")
    serial = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field,
            }),
            label="Serial number, MAC or WWN")
    barcode = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field,
            }))
    position = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12',
                'title': TooltipContent.empty_field,
            }),
            label="Datacenter, rack or position")
    history = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class':'span12'
            }))
    device_type = forms.MultipleChoiceField(required=False,
            widget=forms.SelectMultiple(attrs={'class': 'span12'}),
            choices=DeviceType(item=lambda e: (e.id, e.raw)),
            )
    device_group = forms.IntegerField(required=False,
            widget=DeviceGroupWidget, label="")
    component_group = forms.IntegerField(required=False,
            widget=ComponentGroupWidget, label="")
    purchase_date_start = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12',
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='Purchase date', input_formats=['%Y-%m-%d'])
    purchase_date_end = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12 end-date-field',
            'placeholder': 'End YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='', input_formats=['%Y-%m-%d'])
    no_purchase_date = forms.BooleanField(required=False,
        label="Empty purchase date",
        widget=forms.CheckboxInput(attrs={
            'data-collapsed': True,
        }))
    deprecation_date_start = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12',
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='Deprecation date', input_formats=['%Y-%m-%d'])
    deprecation_date_end = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12 end-date-field',
            'placeholder': 'End YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='', input_formats=['%Y-%m-%d'])
    no_deprecation_date = forms.BooleanField(required=False,
        label="Empty deprecation date",
        widget=forms.CheckboxInput(attrs={
            'data-collapsed': True,
        }))
    warranty_expiration_date_start = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12',
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='Warranty expiration date', input_formats=['%Y-%m-%d'])
    warranty_expiration_date_end = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12 end-date-field',
            'placeholder': 'End YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='', input_formats=['%Y-%m-%d'])
    no_warranty_expiration_date = forms.BooleanField(required=False,
        label="Empty warranty expiration date",
        widget=forms.CheckboxInput(attrs={
            'data-collapsed': True,
        }))
    support_expiration_date_start = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12',
            'placeholder': 'Start YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='Support expiration date', input_formats=['%Y-%m-%d'])
    support_expiration_date_end = forms.DateField(required=False,
        widget=DateWidget(attrs={
            'class':'span12 end-date-field ',
            'placeholder': 'End YYYY-MM-DD',
            'data-collapsed': True,
        }),
        label='', input_formats=['%Y-%m-%d'])
    no_support_expiration_date = forms.BooleanField(required=False,
        label="Empty support expiration date",
        widget=forms.CheckboxInput(attrs={
            'data-collapsed': True,
        }))
    deleted = forms.BooleanField(required=False, label="Include deleted")

    def clean_purchase_date_end(self):
        validate_start_end_date_date(self.cleaned_data['purchase_date_start'],
            self.cleaned_data['purchase_date_end'])
        return self.cleaned_data['purchase_date_end']

    def clean_deprecation_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['deprecation_date_start'],
            self.cleaned_data['deprecation_date_end'])
        return self.cleaned_data['deprecation_date_end']

    def clean_warranty_expiration_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['warranty_expiration_date_start'],
            self.cleaned_data['warranty_expiration_date_end'])
        return self.cleaned_data['warranty_expiration_date_end']

    def clean_support_expiration_date_end(self):
        validate_start_end_date_date(
            self.cleaned_data['support_expiration_date_start'],
            self.cleaned_data['support_expiration_date_end'])
        return self.cleaned_data['support_expiration_date_end']

    def clean_address(self):
        data = self.cleaned_data['address']
        if data:
            if '/' in data:
                try:
                    ipaddr.IPNetwork(data)
                except ValueError:
                    raise forms.ValidationError("Invalid network")
            else:
                try:
                    ipaddr.IPv4Address(data)
                except ValueError:
                    raise forms.ValidationError("Invalid address")
        return data

class PropertyForm(forms.Form):
    icons = {}

    def __init__(self, properties, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        for p in properties:
            if p.type is None:
                field = forms.CharField(label=p.symbol, required=False)
            else:
                choices = [(tv.value, tv.value) for tv in
                           p.type.rolepropertytypevalue_set.all()]
                field = forms.ChoiceField(label=p.symbol, required=False,
                                          choices=choices)
            self.fields[p.symbol] = field


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


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        widgets = {
            'parent': DeviceWidget,
            'model': DeviceModelWidget,
            'rack': RackWidget,
            'dc': RackWidget,
            'cached_price': ReadOnlyPriceWidget,
            'cached_cost': ReadOnlyPriceWidget,
            'auto_price': ReadOnlyPriceWidget,
            'purchase_date': DateWidget,
            'deprecation_date': ReadOnlyWidget,
            'warranty_expiration_date': DateWidget,
            'support_expiration_date': DateWidget,
        }

    save_comment = forms.CharField(required=True,
            help_text="Describe your change",
            error_messages={
                'required': "You must describe your change",
            },
        )

    icons = {
        'name': 'fugue-network-ip',
        'barcode': 'fugue-barcode',
        'position': 'fugue-map',
        'chassis_position': 'fugue-map-pin',
        'model': 'fugue-wooden-box',
        'model_name': 'fugue-wooden-box',
        'venture': 'fugue-store',
        'venture_role': 'fugue-mask',
        'verified': 'fugue-tick',
        'dc': 'fugue-building',
        'dc_name': 'fugue-building',
        'rack': 'fugue-media-player-phone',
        'rack_name': 'fugue-media-player-phone',
        'remarks': 'fugue-sticky-note',
        'price': 'fugue-money-coin',
        'auto_price': 'fugue-money-coin',
        'margin_kind': 'fugue-piggy-bank',
        'deprecation_kind': 'fugue-bin',
        'cached_price': 'fugue-receipt-invoice',
        'cached_cost': 'fugue-receipt-text',
        'purchase_date': 'fugue-baggage-cart-box',
        'warranty_expiration_date': 'fugue-sealing-wax',
        'sn': 'fugue-wooden-box-label',
        'support_expiration_date': 'fugue-hammer-screwdriver',
        'support_kind': 'fugue-hammer-screwdriver',
        'deleted': 'fugue-skull',
    }

    def manual_fields(self):
        device = self.instance
        fields = []
        for field, priority in device.get_save_priorities().iteritems():
            if priority < 100:
                continue
            if field.endswith('_id'):
                field = field[:-3]
            if field in ('parent', 'model', 'role'):
                continue
            fields.append(field)
        return fields

    def clean_cached_price(self):
        return self.instance.cached_price

    def clean_cached_cost(self):
        return self.instance.cached_cost

    def clean_model(self):
        return self.instance.model

    def clean_dc(self):
        return self.instance.dc

    def clean_rack(self):
        return self.instance.rack

    def clean_parent(self):
        return self.instance.parent

    def clean_verified(self):
        verified = self.cleaned_data['verified']
        if verified and not (self.cleaned_data['venture'] and
                             self.cleaned_data['venture_role']):
            raise forms.ValidationError("Can't verify an empty role!")
        return verified

    def clean_barcode(self):
        barcode = self.cleaned_data['barcode']
        return barcode or None

    def clean_sn(self):
        sn = self.cleaned_data['sn']
        return sn or None

    def clean_venture_role(self):
        role = self.cleaned_data.get('venture_role')
        venture = self.cleaned_data.get('venture')
        if role and venture and role.venture == venture:
            return role
        if role is not None:
            raise forms.ValidationError("Role from a different venture.")
        return None


class DeviceCreateForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        widgets = {
            'model': None,
            'purchase_date': DateWidget,
            'warranty_expiration_date': DateWidget,
            'support_expiration_date': DateWidget,
        }
        fields = (
            'name',
            'venture',
            'venture_role',
            'barcode',
            'position',
            'chassis_position',
            'remarks',
            'margin_kind',
            'deprecation_kind',
            'price',
            'model',
            'sn',
            'barcode',
            'purchase_date',
            'warranty_expiration_date',
            'support_expiration_date',
            'support_kind',
        )

    macs = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(DeviceCreateForm, self).__init__(*args, **kwargs)
        self.fields['venture'].choices = _all_ventures()
        self.fields['venture_role'].choices = _all_roles()
        self.fields['venture'].required = True
        self.fields['model'].required = True
        del self.fields['save_comment']

    def clean_macs(self):
        sn = self.cleaned_data['sn']
        macs_text = self.cleaned_data['macs']
        macs = []
        for mac in macs_text.split(' \r\n\t,;'):
            if not mac:
                continue
            try:
                eth = Eth('', MACAddressField.normalize(mac), 0)
                if is_mac_valid(eth):
                    macs.append(eth.mac)
            except ValueError as e:
                raise forms.ValidationError(e)
        if not (macs or sn):
            raise forms.ValidationError(
                    "Either MACs or serial number required.")
        return ' '.join(macs)

    def clean_model(self):
        return self.cleaned_data['model']


class DeviceBulkForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        fields = (
            'venture',
            'venture_role',
            'verified',
            'barcode',
            'position',
            'chassis_position',
            'remarks',
            'margin_kind',
            'deprecation_kind',
            'price',
            'sn',
            'barcode',
            'purchase_date',
            'warranty_expiration_date',
            'support_expiration_date',
            'support_kind',
            'deleted',
        )

    def __init__(self, *args, **kwargs):
        super(DeviceBulkForm, self).__init__(*args, **kwargs)
        self.fields['venture'].choices = _all_ventures()
        self.fields['venture_role'].choices = _all_roles()


class DeviceInfoForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        fields = (
            'name',
            'model',
            'venture',
            'venture_role',
            'verified',
            'barcode',
            'dc',
            'rack',
            'position',
            'chassis_position',
            'parent',
            'remarks',
            'deleted',
        )

    def __init__(self, *args, **kwargs):
        super(DeviceInfoForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            self.data['model_name'] = self.initial['model_name']
            self.data['rack_name'] = self.initial['rack_name']
            self.data['dc_name'] = self.initial['dc_name']
        self.fields['venture'].choices = _all_ventures()
        self.fields['venture_role'].choices = _all_roles()


class DeviceInfoVerifiedForm(DeviceInfoForm):
    class Meta(DeviceInfoForm.Meta):
        fields = [field for field in
                  DeviceInfoForm.Meta.fields if field != 'verified']
        widgets = {
            'venture': ReadOnlySelectWidget,
            'venture_role': ReadOnlySelectWidget,
            'parent': DeviceWidget,
            'model': DeviceModelWidget,
            'rack': RackWidget,
            'dc': RackWidget,
            'cached_price': ReadOnlyPriceWidget,
            'cached_cost': ReadOnlyPriceWidget,
            'auto_price': ReadOnlyPriceWidget,
            'purchase_date': DateWidget,
            'deprecation_date': ReadOnlyWidget,
            'warranty_expiration_date': DateWidget,
            'support_expiration_date': DateWidget,
        }

    def clean_venture(self):
        return self.instance.venture

    def clean_venture_role(self):
        return self.instance.venture_role


class DevicePricesForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        fields = (
            'margin_kind',
            'deprecation_kind',
            'cached_price',
            'cached_cost',
            'price',
        )

    auto_price = forms.CharField(widget=ReadOnlyPriceWidget, required=False)

    def __init__(self, *args, **kwargs):
        super(DevicePricesForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            for field in ('cached_price', 'cached_cost'):
                self.data[field] = getattr(self.instance, field)
            self.data['auto_price'] = self.initial['auto_price']


class DevicePurchaseForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        fields = (
            'model_name',
            'sn',
            'barcode',
            'purchase_date',
            'deprecation_date',
            'warranty_expiration_date',
            'support_expiration_date',
            'support_kind',
        )

    def clean_deprecation_date(self):
        return self.instance.deprecation_date

    def __init__(self, *args, **kwargs):
        super(DevicePurchaseForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            self.data['model_name'] = self.initial['model_name']

    model_name = forms.CharField(label="Model", widget=ReadOnlyWidget,
                                 required=False)
