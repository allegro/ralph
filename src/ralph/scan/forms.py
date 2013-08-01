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


class DiffSelect(forms.Select):
    """A widget for selecting one of the values of a diff."""

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        output = []
        for option, label in self.choices:
            output.append('<label class="radio">')
            if value in option.split(', '):
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
    Widget = forms.TextInput


class ListInfo(DefaultInfo):
    display = ', '.join
    Widget = forms.Textarea


class AssetInfo(DefaultInfo):
    display = operator.attrgetter('name')
    Widget = None

    @classmethod
    def Field(cls, *args, **kwargs):
        kwargs.update(help_text = "Enter barcode or serial number.")
        lookup = ('ralph_assets.models', 'AssetLookup')
        return AutoCompleteSelectField(lookup, *args, **kwargs)


class DiffForm(forms.Form):
    """Form for selecting the results of a scan."""

    field_info = {
        'mac_addresses': ListInfo,
        'management_ip_addresses': ListInfo,
        'system_ip_addresses': ListInfo,
        'asset': AssetInfo,
    }


    def __init__(self, data, *args, **kwargs):
        super(DiffForm, self).__init__(*args, **kwargs)
        for field_name, values in sorted(data.iteritems()):
            info = self.field_info.get(field_name, DefaultInfo)
            choices = [
                (', '.join(sorted(sources)), info.display(value))
                for (sources, value) in values.iteritems()
            ]
            field = forms.ChoiceField(
                label=field_name.replace('_', ' ').title(),
                choices=choices,
                widget=DiffSelect,
            )
            field.initial = 'database'
            self.fields[field_name] = field
            subfield = info.Field(widget=info.Widget)
            field.subfield_name = '%s-custom' % field_name
            self.fields[field.subfield_name] = subfield
