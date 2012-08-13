# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.template.defaultfilters import slugify
from bob.forms import AutocompleteWidget
from lck.django.common.models import MACAddressField

from ralph.discovery.models import (Device, ComponentModelGroup, DeviceModel,
                                    DeviceModelGroup, DeviceType)
from ralph.business.models import Venture, RoleProperty, VentureRole
from ralph.discovery.models_component import is_mac_valid
from ralph.util import Eth, presentation


class ReadOnlySelectWidget(forms.Select):
    def _has_changed(self, initial, data):
        return False

    def render(self, name, value, attrs=None, choices=()):
        labels = dict(self.choices)
        value = unicode(labels.get(value, ''))
        return mark_safe('<div class="input uneditable-input">%s</div>' % value)


class ReadOnlyPriceWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        try:
            value = int(round(value))
            value = '{:,.0f} {}'.format(value, settings.CURRENCY).replace(',', ' ')
        except (ValueError, TypeError):
            pass
        return mark_safe(
            '<div class="input uneditable-input currency">%s</div>' % value)

class ReadOnlyMultipleChoiceWidget(FilteredSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        output_values = []
        choices = dict([x for x in self.choices])
        for v in value:
            output_values.append(choices.get(v,''))
        return mark_safe('<div class="input uneditable-input">%s</div>' %
                ','.join(output_values))

class ReadOnlyWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        return mark_safe('<div class="input uneditable-input">%s</div>' % value)


class DeviceModelWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        dm = None
        if value:
            try:
                dm = DeviceModel.objects.get(id=value)
            except DeviceModel.DoesNotExist:
                pass
        if dm is None:
            output = [
                '<input type="hidden" name="%s" value="">' % (name,),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_model_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (name, value),
                '<div class="input uneditable-input">',
                '<a href="/admin/discovery/devicemodel/%s">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (dm.id,
                    presentation.get_device_model_icon(dm), dm.name),
                '</div>',
            ]
        return mark_safe('\n'.join(output))


class DeviceWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        dev = None
        if value:
            try:
                dev = Device.objects.get(id=value)
            except Device.DoesNotExist:
                pass
        if dev is None:
            output = [
                '<input type="hidden" name="%s" value="">' % (name,),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (name, value),
                '<div class="input uneditable-input">',
                '<a href="%s">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (dev.id,
                    presentation.get_device_icon(dev), dev.name),
                '</div>',
            ]
        return mark_safe('\n'.join(output))


class RackWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        dev = None
        if value:
            try:
                dev = Device.objects.get(sn=(value or '').lower())
            except Device.DoesNotExist:
                pass
        if dev is None:
            output = [
                '<input type="hidden" name="%s" value="">' % (name,),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (name, value),
                '<div class="input uneditable-input">',
                '<a href="/ui/racks/%s/info/">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (slugify(dev.sn),
                    presentation.get_device_icon(dev), dev.name),
                '</div>',
            ]
        return mark_safe('\n'.join(output))



class ComponentGroupWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        try:
            mg = ComponentModelGroup.objects.get(id=value)
        except ComponentModelGroup.DoesNotExist:
            output = [
            ]
        else:
            output = [
                '<label class="checkbox">',
                '<input type="checkbox" checked="checked" name="%s" value="%s">' % (name, value),
                '<a href="../../catalog/component/%s/%s">%s</a>' % (mg.type, mg.id, mg.name),
                '</label>',
            ]
        return mark_safe('\n'.join(output))


class DeviceGroupWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        try:
            mg = DeviceModelGroup.objects.get(id=value)
        except DeviceModelGroup.DoesNotExist:
            output = [
            ]
        else:
            output = [
                '<label class="checkbox">',
                '<input type="checkbox" checked="checked" name="%s" value="%s">' % (name, value),
                '<a href="../../catalog/device/%s/%s">%s</a>' % (mg.type, mg.id, mg.name),
                '</label>',
            ]
        return mark_safe('\n'.join(output))


class DateWidget(forms.DateInput):
    input_type = 'text'


class DateRangeForm(forms.Form):
    start = forms.DateField(widget=DateWidget)
    end = forms.DateField(widget=DateWidget)


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
                choices = [(tv.value, tv.value) for tv in p.type.rolepropertytypevalue_set.all()]
                field = forms.ChoiceField(label=p.symbol, required=False, choices=choices)
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

    def _all_ventures(self):
        ventures = [(v.id, v.name) for v in
                Venture.objects.filter(
                    show_in_ralph=True
                ).order_by(
                    '-is_infrastructure', 'name'
                )]
        ventures.insert(0, ('', '---------'))
        return ventures

    def _all_roles(self):
        roles = [(r.id, '%s / %s' % (r.venture.name, r.full_name))
                for r in VentureRole.objects.order_by(
                    '-venture__is_infrastructure', 'venture__name',
                    'parent__parent__name', 'parent__name', 'name'
                )
            ]
        roles.insert(0, ('', '---------'))
        return roles

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
        self.fields['venture'].choices = self._all_ventures()
        self.fields['venture_role'].choices = self._all_roles()
        self.fields['venture'].required = True
        self.fields['model'].required = True
        del self.fields['save_comment']

    def clean_macs(self):
        sn = self.cleaned_data['sn']
        macs_text = self.cleaned_data['macs']
        macs = []
        for mac in macs_text.split(' \r\n\t,;'):
            try:
                eth = Eth('', MACAddressField.normalize(mac), 0)
                if is_mac_valid(eth):
                    macs.append(eth.mac)
            except ValueError as e:
                raise forms.ValidationError(e)
        if not (macs or sn):
            raise forms.ValidationError("Either MACs or serial number required.")
        return ' '.join(macs)

    def clean_model(self):
        return self.cleaned_data['model']


class DeviceBulkForm(DeviceForm):
    class Meta(DeviceForm.Meta):
        fields = (
            'venture',
            'venture_role',
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
        self.fields['venture'].choices = self._all_ventures()
        self.fields['venture_role'].choices = self._all_roles()

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
        self.fields['venture'].choices = self._all_ventures()
        self.fields['venture_role'].choices = self._all_roles()


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
            'warranty_expiration_date',
            'support_expiration_date',
            'support_kind',
        )

    def __init__(self, *args, **kwargs):
        super(DevicePurchaseForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            self.data['model_name'] = self.initial['model_name']

    model_name = forms.CharField(label="Model", widget=ReadOnlyWidget, required=False)
