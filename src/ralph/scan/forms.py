# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import operator

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import escape, conditional_escape
from ajax_select.fields import AutoCompleteSelectField

from ralph.discovery.models import DeviceType


class WidgetTable(forms.MultiWidget):
    def __init__(self, headers, rows, attrs=None):
        self.rows = rows
        self.headers = headers
        widgets = []
        for i in xrange(self.rows):
            for h in self.headers:
                widgets.append(forms.TextInput(attrs=attrs))
        super(WidgetTable, self).__init__(widgets, attrs)

    def decompress(self, value):
        values = []
        for row in value or []:
            for h in self.headers:
                values.append(row.get(h, ''))
        values.extend([''] * (self.rows - len(value or [])) * len(self.headers))
        return values

    def format_output(self, rendered_widgets):
        widgets = iter(rendered_widgets)
        output = [
            '<table class="table table-condensed table-bordered" style="width:auto; display:inline-block;vertical-align: top;">',
            '<tr>',
            '<th>#</th>',
        ]
        for h in self.headers:
            output.append('<th>%s</th>' % escape(h.replace('_', ' ').title()))
        output.append('</tr>')
        for i in xrange(self.rows):
            output.append('<tr>')
            output.append('<td>%d</td>' % (i + 1))
            for h in self.headers:
                output.append('<td>%s</td>' % widgets.next())
            output.append('</tr>')
        output.append('</table>')
        return '\n'.join(output)

    def value_from_datadict(self, data, files, name):
        values = iter(
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)
        )
        value = []
        for i in xrange(self.rows):
            line = {}
            for h in self.headers:
                line[h] = values.next()
            value.append(line)
        return value


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
            output.append(conditional_escape(label))
            output.append(' (from <i>%s</i>)' % escape(option))
            output.append('</label>')
        return mark_safe('\n'.join(output))


class DefaultInfo(object):
    display = unicode
    Field = forms.CharField
    Widget = None
    clean = unicode

class ListInfo(DefaultInfo):
    display = ', '.join
    Widget = forms.Textarea

    def clean(self, value):
        return value.replace(',', ' ').split()

class DictListInfo(ListInfo):
    def __init__(self, headers, rows):
        self.headers = headers
        self.rows = rows

    def display(self, value):
        if not self.headers:
            keyset = set()
            for d in value:
                keyset |= set(d)
            self.headers = sorted(keyset)
        output = [
                '<table class="table table-condensed table-bordered" style="width:auto; display:inline-block;vertical-align: top;">',
            '<tr>',
            '<th>#</th>',
            ''.join(
                '<th>%s</th>' % escape(h.replace('_', ' ').title())
                for h in self.headers
            ),
            '</tr>',
        ]
        for i, d in enumerate(value):
            line = []
            line.append('<tr>')
            line.append('<td>%d</td>' % (i + 1))
            for h in self.headers:
                line.append('<td>%s</td>' % d.get(h, ''))
            line.append('</tr>')
            output.append(''.join(line))
        output.append('</table>')
        return mark_safe('\n'.join(output))

    @property
    def Widget(self):
        return WidgetTable(self.headers, self.rows)


class AssetInfo(DefaultInfo):
    display = operator.attrgetter('name')
    Widget = None

    def clean(self, value):
        return value

    def Field(self, *args, **kwargs):
        kwargs.update(help_text="Enter barcode or serial number.")
        lookup = ('ralph_assets.models', 'AssetLookup')
        return AutoCompleteSelectField(lookup, *args, **kwargs)


class TypeInfo(DefaultInfo):
    def Field(self, *args, **kwargs):
        choices = [
            (t.raw, t.raw.title())
            for t in DeviceType(item=lambda t: t)
        ]
        # Make "Unknown" the first choice
        choices.insert(0, choices.pop())
        kwargs['choices'] = choices
        return forms.ChoiceField(*args, **kwargs)


class RequiredInfo(DefaultInfo):
    def clean(self, value):
        if not value:
            raise ValueError('This field is required.')
        return value


class DiffForm(forms.Form):
    """Form for selecting the results of a scan."""

    field_info = {
        'mac_addresses': ListInfo(),
        'management_ip_addresses': ListInfo(),
        'system_ip_addresses': ListInfo(),
        'asset': AssetInfo(),
        'type': TypeInfo(),
        'model_name': RequiredInfo(),
        'disks': DictListInfo(['model', 'serial_number', 'size'], 4),
    }


    def __init__(self, data, *args, **kwargs):
        try:
            default = kwargs.pop('default')
        except KeyError:
            default = 'custom'
        super(DiffForm, self).__init__(*args, **kwargs)
        self.result = data
        for field_name, values in sorted(data.iteritems()):
            info = self.field_info.get(field_name, DefaultInfo())
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
                info = self.field_info.get(name, DefaultInfo())
                try:
                    value = info.clean(self.cleaned_data[name + '-custom'])
                except (TypeError, ValueError, forms.ValidationError) as e:
                    self._errors[name + '-custom'] = self.error_class([e])
        return self.cleaned_data

    def get_value(self, name):
        value = self.cleaned_data[name]
        if value == 'custom':
            info = self.field_info.get(name, DefaultInfo())
            return info.clean(self.cleaned_data[name + '-custom'])
        key = tuple(value.split(', '))
        return self.result[name][key]

