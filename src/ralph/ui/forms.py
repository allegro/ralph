# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from calendar import monthrange
from django import forms
from lck.django.common.models import MACAddressField
from bob.forms import AutocompleteWidget

from ralph.business.models import Venture, RoleProperty, VentureRole
from ralph.deployment.models import Deployment
from ralph.discovery.models_component import is_mac_valid

from ralph.discovery.models import (Device, ComponentModelGroup,DeviceModelGroup,
                                    DeviceType, IPAddress)
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import is_valid_hostname
from ralph.util import Eth
from ralph.ui.widgets import (DateWidget, YearsBarWidget, MonthsBarWidget,
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
                        'class': 'span2',
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
            widget=forms.TextInput(attrs={'class':'span2'}))


class SearchForm(forms.Form):
    name = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}))
    address = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}),
            label="Address or network")
    remarks = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}))
    role = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}),
            label="Venture or role")
    model = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}))
    component = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}),
            label="Component or software")
    serial = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}),
            label="Serial number or MAC")
    barcode = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}))
    position = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}),
            label="Datacenter, rack or position")
    history = forms.CharField(required=False,
            widget=forms.TextInput(attrs={'class':'span2'}))
    device_type = forms.MultipleChoiceField(required=False,
            widget=forms.SelectMultiple(attrs={'class': 'span2'}),
            choices=DeviceType(item=lambda e: (e.id, e.raw)),
            )
    device_group = forms.IntegerField(required=False,
            widget=DeviceGroupWidget, label="")
    component_group = forms.IntegerField(required=False,
            widget=ComponentGroupWidget, label="")
    deleted = forms.BooleanField(required=False,
            label="Include deleted")


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


class ComponentModelGroupForm(forms.ModelForm):
    class Meta:
        model = ComponentModelGroup
        exclude = ['type']

    icons = {
        'name': 'fugue-paper-bag',
        'price': 'fugue-money-coin',
        'per_size': 'fugue-ruler',
    }
    has_delete = True


class DeviceModelGroupForm(forms.ModelForm):
    class Meta:
        model = DeviceModelGroup
        exclude = ['type']

    icons = {
        'name': 'fugue-paper-bag',
        'price': 'fugue-money-coin',
        'slots': 'fugue-drawer',
    }
    has_delete = True


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
            widget=forms.TextInput(attrs={'class':'span4'}),
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
