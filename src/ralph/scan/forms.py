# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import operator

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import escape
from ajax_select.fields import AutoCompleteSelectField

from ralph.discovery.models import DeviceType


class DiffSelect(forms.Select):
    """A widget for selecting one of the values of a diff."""

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        output = []
        for option, label in self.choices:
            if option == 'custom':
                continue
            output.append('<label class="radio">')
            if value == option or value in option.split(', '):
                html_input = '<input type="radio" name="%s" value="%s" checked="on">'
            else:
                html_input = '<input type="radio" name="%s" value="%s">'
            output.append(html_input % (escape(name), escape(option)))
            output.append('<b>%s</b>' % escape(label))
            output.append(' (from <i>%s</i>)' % escape(option))
            output.append('</label>')
        return mark_safe(u'\n'.join(output))


class DefaultInfo(object):
    display = unicode
    Field = forms.CharField
    Widget = None
    clean = unicode


class ListInfo(DefaultInfo):
    display = ', '.join
    Widget = forms.Textarea

    @staticmethod
    def clean(value):
        return value.replace(',', ' ').split()


class AssetInfo(DefaultInfo):
    display = operator.attrgetter('name')
    Widget = None

    @staticmethod
    def clean(value):
        return value

    @classmethod
    def Field(cls, *args, **kwargs):
        kwargs.update(help_text="Enter barcode or serial number.")
        lookup = ('ralph_assets.models', 'AssetLookup')
        return AutoCompleteSelectField(lookup, *args, **kwargs)


class TypeInfo(DefaultInfo):
    @classmethod
    def Field(cls, *args, **kwargs):
        choices = [
            (t.raw, t.raw.title())
            for t in DeviceType(item=lambda t: t)
        ]
        # Make "Unknown" the first choice
        choices.insert(0, choices.pop())
        kwargs['choices'] = choices
        return forms.ChoiceField(*args, **kwargs)


class RequiredInfo(DefaultInfo):
    @staticmethod
    def clean(value):
        if not value:
            raise ValueError('This field is required.')
        return value


class DiffForm(forms.Form):
    """Form for selecting the results of a scan."""

    field_info = {
        'mac_addresses': ListInfo,
        'management_ip_addresses': ListInfo,
        'system_ip_addresses': ListInfo,
        'asset': AssetInfo,
        'type': TypeInfo,
        'model_name': RequiredInfo,
    }


    def __init__(self, data, *args, **kwargs):
        try:
            default = kwargs.pop('default')
        except KeyError:
            default = 'custom'
        super(DiffForm, self).__init__(*args, **kwargs)
        self.result = data
        for field_name, values in sorted(data.iteritems()):
            info = self.field_info.get(field_name, DefaultInfo)
            choices = [
                (', '.join(sorted(sources)), info.display(value))
                for (sources, value) in values.iteritems()
            ]
            choices.append(('custom', ''))
            field = forms.ChoiceField(
                label=field_name.replace('_', ' ').title(),
                choices=choices,
                widget=DiffSelect,
            )
            field.initial = default
            self.fields[field_name] = field
            subfield = info.Field(widget=info.Widget, required=False)
            field.subfield_name = '%s-custom' % field_name
            self.fields[field.subfield_name] = subfield

    def clean(self):
        for name, value in self.cleaned_data.iteritems():
            if name.endswith('-custom'):
                continue
            if value == 'custom':
                info = self.field_info.get(name, DefaultInfo)
                try:
                    value = info.clean(self.cleaned_data[name + '-custom'])
                except (TypeError, ValueError, forms.ValidationError) as e:
                    self._errors[name + '-custom'] = self.error_class([e])
        return self.cleaned_data

    def get_value(self, name):
        value = self.cleaned_data[name]
        if value == 'custom':
            info = self.field_info.get(name, DefaultInfo)
            return info.clean(self.cleaned_data[name + '-custom'])
        key = tuple(value.split(', '))
        return self.result[name][key]

