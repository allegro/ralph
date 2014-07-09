# -*- coding: utf-8 -*-

"""
Forms and widgets to act with Scan results.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools

from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe

from ralph.discovery.models import DeviceType


class CSVWidget(forms.Widget):

    def __init__(self, headers, attrs=None):
        self.headers = headers
        super(CSVWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = [
            '<textarea name="%s" rows="10" style="width:90%%; font-family: monospace">' % escape(
                name),
            escape(';'.join(h.rjust(16) for h in self.headers)),
        ]
        for row in value or []:
            output.append(escape(';'.join(
                row.get(h, '') or ''
                for h in self.headers
            )))
        output.append('</textarea>'),
        return mark_safe('\n'.join(output))

    def value_from_datadict(self, data, files, name):
        field_data = data[name]
        values = []
        for line in field_data.splitlines():
            if not line.strip():
                continue
            row = {}
            row_values = [v.strip() for v in line.split(';')]
            if not any(row_values):
                continue
            if row_values == self.headers:
                continue
            for h, value in itertools.izip_longest(self.headers, row_values):
                row[h] = value
            values.append(row)
        return values


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
        values.extend(
            [''] * (self.rows - len(value or [])) * len(self.headers))
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

    """
    A widget used to:
    - display diff of results
    - select one of the possible scan choices (also DB)
    - display change summary
    """

    def __init__(self, diff=None, default_value=None, *args, **kwargs):
        self.diff = diff
        self.default_value = default_value
        self.open_advanced_mode = False
        super(DiffSelect, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        self.open_advanced_mode = self.default_value != value
        return render_to_string(
            'scan/widgets/diff_select.html',
            {
                'choices': self.choices,
                'name': name,
                'value': value,
                'diff': self.diff,
                'open_advanced_mode': self.open_advanced_mode,
            },
        )


class DefaultInfo(object):
    display = unicode
    Field = forms.CharField
    Widget = None
    clean = unicode


class RequiredInfo(DefaultInfo):

    def clean(self, value):
        if not value:
            raise ValueError('This field is required.')
        return value


class IntInfo(DefaultInfo):
    display = int
    Field = forms.IntegerField
    clean = int


class ListInfo(DefaultInfo):
    display = ', '.join
    Field = forms.Field
    Widget = forms.Textarea

    def clean(self, value):
        return value.replace(',', ' ').split()


class CSVInfo(DefaultInfo):
    Field = forms.Field

    def __init__(self, headers):
        self.headers = headers

    def _get_cols_width(self, values):
        width = 14
        for row in values:
            for header in self.headers:
                header_len = len(header)
                if header_len > width:
                    width = header_len
                value_len = len(unicode(row.get(header, '')))
                if value_len > width:
                    width = value_len
        width += 2
        return width

    def display(self, value):
        cols_width = self._get_cols_width(value)
        output = [
            '<pre class="scan-display-results-for-component">',
            '<b>%s</b>' % escape(
                ';'.join((' %s' % h).ljust(cols_width) for h in self.headers),
            ),
            escape('\n'.join(';'.join(
                unicode((' %s' % (row.get(h, '') or ''))).ljust(cols_width)
                for h in self.headers) for row in value
            )),
            '</pre>',
        ]
        return mark_safe('\n'.join(output))

    @property
    def Widget(self):
        return CSVWidget(self.headers)

    def clean(self, value):
        return value


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
    Widget = None

    def clean(self, value):
        if not value:
            raise ValueError('You have to select an asset for device.')
        return value

    def Field(self, *args, **kwargs):
        kwargs.update(help_text="Enter barcode, model or serial number.")
        lookup = ('ralph_assets.api_ralph', 'AssetLookupFuzzy')
        return AutoCompleteSelectField(lookup, *args, **kwargs)


class TypeInfo(RequiredInfo):

    def Field(self, *args, **kwargs):
        choices = [
            (t.raw, t.raw.title())
            for t in DeviceType(item=lambda t: t)
        ]
        choices.pop()  # remove "Unknown" from the list
        choices.insert(0, ('', '-----'))
        kwargs['choices'] = choices
        return forms.ChoiceField(*args, **kwargs)


class DiffForm(forms.Form):

    """Form for selecting the results of a scan."""

    field_info = {
        'mac_addresses': ListInfo(),
        'management_ip_addresses': ListInfo(),
        'system_ip_addresses': ListInfo(),
        'asset': AssetInfo(),
        'type': TypeInfo(),
        'model_name': RequiredInfo(),
        'chassis_position': IntInfo(),
        'disks': CSVInfo([
            'label',
            'model_name',
            'family',
            'serial_number',
            'size',
            'speed',
            'mount_point',
        ]),
        'memory': CSVInfo(['size', 'speed', 'label']),
        'processors': CSVInfo(['family', 'speed', 'cores', 'label']),
        'disk_exports': CSVInfo([
            'model_name',
            'serial_number',
            'full', 'size',
            'snapshot_size',
            'share_id',
            'label',
        ]),
        'disk_shares': CSVInfo([
            'serial_number',
            'address',
            'is_virtual',
            'size',
            'volume',
            'server',
        ]),
        'installed_software': CSVInfo([
            'model_name',
            'version',
            'serial_number',
            'path',
            'label',
        ]),
        'fibrechannel_cards': CSVInfo(['model_name', 'physical_id', 'label']),
        'parts': CSVInfo([
            'model_name',
            'type',
            'serial_number',
            'label',
            'boot_firmware',
            'hard_firmware',
            'diag_firmware',
            'mgmt_firmware',
        ]),
        'subdevices': CSVInfo(['hostname', 'serial_number', 'id']),
    }

    def __init__(self, data, *args, **kwargs):
        diff = kwargs.pop('diff', None)
        default = kwargs.pop('default', 'custom')
        csv_default = kwargs.pop('csv_default', 'custom')
        super(DiffForm, self).__init__(*args, **kwargs)
        self.result = data
        for field_name, values in sorted(data.iteritems()):
            info = self.field_info.get(field_name, DefaultInfo())
            choices = [
                (
                    ', '.join(sorted(sources)),
                    info.display(value),
                ) for (sources, value) in values.iteritems()
            ]
            choices.append(('custom', ''))
            if isinstance(info, CSVInfo):
                default_value = csv_default
            else:
                default_value = default
            default_in_choices = False
            for plugin_name, value in choices:
                if default_value in plugin_name:
                    default_in_choices = True
                    break
            if not default_in_choices:
                default_value = 'database'
            field = forms.ChoiceField(
                label=field_name.replace('_', ' ').title(),
                choices=choices,
                widget=DiffSelect(
                    diff=diff.get(field_name) if diff else None,
                    default_value=default_value,
                ),
            )
            field.initial = default_value
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
            else:
                if (name == 'type' and
                        self.result['type'].get((value,)) == 'unknown'):
                    msg = "Please specify custom value for this component."
                    self._errors[name] = self.error_class([msg])
        return self.cleaned_data

    def get_value(self, name):
        value = self.cleaned_data[name]
        if value == 'custom':
            info = self.field_info.get(name, DefaultInfo())
            return info.clean(self.cleaned_data[name + '-custom'])
        key = tuple(value.split(', '))
        return self.result[name][key]
