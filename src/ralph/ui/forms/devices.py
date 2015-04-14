# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select.fields import (
    AutoCompleteSelectField,
    CascadeModelChoiceField,
)
from django import forms
from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import MACAddressField

from ralph.deployment.util import get_next_free_hostname
from ralph.discovery.models_component import is_mac_valid
from ralph.discovery.models import (
    ASSET_NOT_REQUIRED,
    Device,
    DeviceEnvironment,
    DeviceType,
)
from ralph.util import Eth
from ralph.ui.widgets import (
    DateWidget,
    ReadOnlySelectWidget,
    DeviceModelWidget,
    ReadOnlyWidget,
    RackWidget,
    ReadOnlyPriceWidget,
)
from ralph.ui.forms.util import all_ventures, all_roles
from ralph_assets.models import Asset, Orientation


class ServiceCatalogMixin(forms.ModelForm):
    # although it is possible, this mixin shouldn't be instantiated on its own
    # (that's why it is still called a mixin, while technically it is a
    # subclass of ModelForm and therefore it *can* be instantiated)
    # -- just try to think of it as an abstract class, ok? ;)

    service = AutoCompleteSelectField(
        ('ralph.ui.channels', 'ServiceCatalogLookup'),
        required=True,
        label=_('Service catalog'),
        # setting widget's id here is necessary for dependent field to work
        attrs={'id': 'service_catalog_ajax_field'},
    )
    device_environment = CascadeModelChoiceField(
        ('ralph.ui.channels', 'DeviceEnvironmentLookup'),
        label=_('Device environment'),
        queryset=DeviceEnvironment.objects.all(),
        parent_field=service,
    )


class DeviceForm(ServiceCatalogMixin):

    class Meta:
        model = Device
        widgets = {
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

    save_comment = forms.CharField(
        required=True,
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

    def __init__(self, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        if self.instance:
            asset = self.instance.get_asset()
            if 'parent' in self.fields:
                self.fields['parent'].choices = [
                    ('', '----'),
                ] + [
                    (p.id, p.name) for p in
                    self.get_possible_parents(self.instance)
                ]
                if asset:
                    self.fields['parent'].widget = ReadOnlySelectWidget(
                        choices=self.fields['parent'].choices,
                    )
            if asset:
                if 'chassis_position' in self.fields:
                    self.fields[
                        'chassis_position'
                    ].widget = ReadOnlyWidget()
                if 'position' in self.fields:
                    self.fields[
                        'position'
                    ].widget = ReadOnlyWidget()

    def get_possible_parents(self, device):
        types = {
            DeviceType.rack,
            DeviceType.data_center,
        }
        if device.model:
            if device.model.type in {DeviceType.blade_server}:
                types = {DeviceType.blade_system}
            elif device.model.type in {DeviceType.virtual_server}:
                types = {
                    DeviceType.rack_server,
                    DeviceType.blade_server,
                }
            elif device.model.type in {DeviceType.rack}:
                types = {DeviceType.data_center}
            elif device.model.type in {
                DeviceType.switch,
                DeviceType.management,
                DeviceType.fibre_channel_switch,
                DeviceType.power_distribution_unit,
            }:
                types.add(DeviceType.blade_system)
        parents = list(
            Device.objects.filter(
                model__type__in=types
            ).order_by('parent', 'sn')
        )
        if device.parent and device.parent not in parents:
            parents.append(device.parent)
        return parents

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

    def clean_deleted(self):
        deleted = self.cleaned_data.get('deleted')
        if deleted:
            if self.instance.child_set.filter(deleted=False).exists():
                raise forms.ValidationError(
                    "You can not remove devices that have children."
                )
        return deleted

    def clean_chassis_position(self):
        chassis_position = self.cleaned_data.get('chassis_position')
        if chassis_position is None:
            return None
        if not 0 <= chassis_position <= 65535:
            raise forms.ValidationError(
                "Invalid numeric position, use range 0 to 65535"
            )
        return chassis_position


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
            'service',
            'device_environment',
            'barcode',
            'chassis_position',
            'position',
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
        self.fields['venture'].choices = all_ventures()
        self.fields['venture_role'].choices = all_roles()
        self.fields['venture'].required = True
        self.fields['model'].required = True
        self.fields['asset'] = AutoCompleteSelectField(
            ('ralph_assets.api_ralph', 'AssetLookup'),
            required=False,
        )
        self.fields['asset'].widget.help_text = (
            'Enter asset sn, barcode or model'
        )
        del self.fields['save_comment']
        if 'data' in kwargs and kwargs['data'].get('asset'):
            if Asset.objects.filter(pk=kwargs['data']['asset']).exists():
                self.fields['chassis_position'].widget = ReadOnlyWidget()
                self.fields['position'].widget = ReadOnlyWidget()

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
                "Either MACs or serial number required."
            )
        return ' '.join(macs)

    def clean_model(self):
        model = self.cleaned_data['model']
        return model or None

    def clean_asset(self):
        model = self.cleaned_data.get('model')
        asset = self.cleaned_data.get('asset')
        # model should be required anyway, so there's no sense to validate an
        # asset when the model is missing
        if not model:
            return asset
        if model and model.type not in ASSET_NOT_REQUIRED:
            if not asset:
                msg = "Asset is required for this kind of device."
                raise forms.ValidationError(msg)
        if 'ralph_assets' in settings.INSTALLED_APPS:
            from ralph_assets.api_ralph import is_asset_assigned
            if asset and is_asset_assigned(asset_id=asset.id):
                raise forms.ValidationError(
                    "This asset is already linked to some other device. "
                    "To resolve this conflict, please click the link above."
                )
        return asset

    def clean(self):
        cleaned_data = super(DeviceCreateForm, self).clean()
        asset = cleaned_data.get('asset')
        if asset:
            # get position from asset
            if all((
                'chassis_position' in cleaned_data,
                asset.device_info.position,
            )):
                cleaned_data['chassis_position'] = asset.device_info.position
            if all((
                'position' in cleaned_data,
                asset.device_info.orientation,
            )):
                cleaned_data['position'] = Orientation.name_from_id(
                    asset.device_info.orientation,
                )
        return cleaned_data


class DeviceBulkForm(DeviceForm):

    class Meta(DeviceForm.Meta):
        fields = (
            'name',
            'venture',
            'venture_role',
            'remarks',
            'deleted',
        )

    def __init__(self, *args, **kwargs):
        super(DeviceBulkForm, self).__init__(*args, **kwargs)
        self.fields['venture'].choices = all_ventures()
        self.fields['venture_role'].choices = all_roles()

    def clean(self):
        if not self.data.get('select'):
            messages.error(
                self.request,
                _("You haven't selected any devices.")
            )


class DeviceInfoForm(DeviceForm):

    class Meta(DeviceForm.Meta):
        fields = (
            'name',
            'model',
            'venture',
            'venture_role',
            'service',
            'device_environment',
            'verified',
            'barcode',
            'dc',
            'rack',
            'chassis_position',
            'position',
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
        self.fields['venture'].choices = all_ventures()
        self.fields['venture_role'].choices = all_roles()
        if not self.instance:
            return
        rack = self.instance.find_rack()
        if rack:
            rack_networks = sorted(
                rack.network_set.all(),
                key=lambda net: net.get_netmask(),
                reverse=True,
            )
            for network in rack_networks:
                if not network.environment:
                    continue
                next_hostname = get_next_free_hostname(network.environment)
                if next_hostname:
                    help_text = 'Next available hostname in this DC: %s' % (
                        next_hostname
                    )
                    self.fields['name'].help_text = help_text
                    break


class DeviceInfoVerifiedForm(DeviceInfoForm):

    class Meta(DeviceInfoForm.Meta):
        fields = [field for field in
                  DeviceInfoForm.Meta.fields if field != 'verified']
        widgets = {
            'venture': ReadOnlySelectWidget,
            'venture_role': ReadOnlySelectWidget,
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


class PropertyForm(forms.Form):
    icons = {}

    def __init__(self, properties, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        for p in properties:
            if p.type is None or p.type.symbol == 'STRING':
                field = forms.CharField(label=p.symbol, required=False)
            elif p.type.symbol == 'INTEGER':
                field = forms.IntegerField(label=p.symbol, required=False)
            else:
                choices = [
                    ('', '------'),
                ] + [
                    (
                        tv.value, tv.value,
                    ) for tv in p.type.rolepropertytypevalue_set.all()
                ]
                field = forms.ChoiceField(
                    label=p.symbol,
                    required=False,
                    choices=choices,
                )
            self.fields[p.symbol] = field
