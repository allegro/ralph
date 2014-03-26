# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import decimal

from django import forms
import ajax_select

from ralph.ui.widgets import CurrencyWidget
from ralph.discovery.models import (
    ComponentModelGroup,
    DeviceModelGroup,
    ComponentType,
)
from ralph.discovery.models_pricing import (
    PricingGroup,
    PricingVariable,
    PricingValue,
    PricingFormula,
)


RESERVED_VARIABLE_NAMES = {'size'}


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

    class Meta(ModelGroupForm.Meta):
        model = ComponentModelGroup
        exclude = ModelGroupForm.Meta.exclude + [
            'price', 'size_modifier', 'size_unit', 'per_size']

    def __init__(self, *args, **kwargs):
        super(ComponentModelGroupForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.per_size:
                modifier = self.instance.size_modifier
                unit = self.instance.size_unit
                if unit == 'MiB' and modifier % 1024 == 0:
                    unit = 'GiB'
                    modifier = int(modifier / 1024)
                price = decimal.Decimal(self.instance.price) / modifier
            else:
                price = self.instance.price
                unit = 'piece'
            self.fields['human_unit'].initial = unit
            self.fields['human_price'].initial = price

    def save(self, *args, **kwargs):
        unit = self.cleaned_data['human_unit']
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


class PricingGroupForm(forms.ModelForm):
    clone = forms.BooleanField(
        label="Clone the last group with that name",
        required=False,
    )
    upload = forms.FileField(
        label="Import a CVS file with variables",
        required=False,
    )

    class Meta:
        model = PricingGroup
        fields = ('name', 'clone', 'upload')

    def __init__(self, date, *args, **kwargs):
        super(PricingGroupForm, self).__init__(*args, **kwargs)
        self.date = date

    def clean_clone(self):
        clone = self.cleaned_data['clone']
        if clone and self.cleaned_data.get('upload'):
            raise forms.ValidationError(
                "Can't clone and import at the same time."
            )
        return clone

    def clean_name(self):
        name = self.cleaned_data['name']
        if PricingGroup.objects.filter(
            name=name,
            date=self.date,
        ).exclude(
            id=self.instance.id
        ).exists():
            raise forms.ValidationError("This group already exists.")
        return name


class PricingDeviceForm(forms.Form):
    device = ajax_select.fields.AutoCompleteSelectField(
        ('ralph.ui.channels', 'DeviceLookup'),
        help_text=None,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PricingDeviceForm, self).__init__(*args, **kwargs)
        self.fields['device'].widget.attrs.update({
            'placeholder': "Add more devices",
            'class': 'span12',
        })


class PricingVariableForm(forms.ModelForm):

    class Meta:
        model = PricingVariable
        fields = ('name', 'aggregate')
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'span12',
                    'placeholder': 'Name',
                }
            ),
            'aggregate': forms.Select(
                attrs={
                    'class': 'span12',
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name.isalpha():
            raise forms.ValidationError(
                "Variable names can only contain letters."
            )
        if name in RESERVED_VARIABLE_NAMES:
            raise forms.ValidationError(
                "Name 'size' is reserved."
            )
        return name

PricingVariableFormSet = forms.models.modelformset_factory(
    PricingVariable,
    form=PricingVariableForm,
    can_delete=True,
)


class PricingValueForm(forms.ModelForm):

    class Meta:
        model = PricingValue
        fields = ('value',)
        widgets = {
            'value': forms.TextInput(
                attrs={
                    'class': 'span12',
                    'placeholder': 'Value',
                },
            ),
        }


PricingValueFormSet = forms.models.modelformset_factory(
    PricingValue,
    form=PricingValueForm,
    extra=0,
)


class PricingFormulaForm(forms.ModelForm):

    class Meta:
        model = PricingFormula
        fields = ('component_group', 'formula')
        widgets = {
            'formula': forms.TextInput(
                attrs={
                    'class': 'span12',
                    'placeholder': 'Formula',
                },
            ),
        }

    def clean_formula(self):
        formula = self.cleaned_data['formula']
        variables = {
            'size': decimal.Decimal(1),
        }
        for variable in self.group.pricingvariable_set.all():
            variables[variable.name] = 1
        try:
            PricingFormula.eval_formula(formula, variables)
        except Exception as e:
            raise forms.ValidationError(e)
        return formula

    def clean_component_group(self):
        component_group = self.cleaned_data['component_group']
        if self.instance and self.group.pricingformula_set.filter(
            component_group=component_group,
        ).exclude(
            id=self.instance.id,
        ).exists():
            raise forms.ValidationError(
                "This component group already has a formula."
            )
        return component_group


class PricingFormulaFormSetBase(forms.models.BaseModelFormSet):

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super(PricingFormulaFormSetBase, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        types = {ComponentType.share}
        form.group = self.group
        form.fields['component_group'].widget.choices = [
            ('', '----'),
        ] + [
            (g.id, g.name) for g in
            ComponentModelGroup.objects.filter(type__in=types)
        ]
        return super(PricingFormulaFormSetBase, self).add_fields(form, index)


PricingFormulaFormSet = forms.models.modelformset_factory(
    PricingFormula,
    form=PricingFormulaForm,
    formset=PricingFormulaFormSetBase,
    can_delete=True,
)
