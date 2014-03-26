# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from django.template.defaultfilters import slugify
from django.utils.html import escape
from django.utils.safestring import mark_safe

from ralph.discovery.models import (DeviceModel, ComponentModelGroup, Device,
                                    DeviceModelGroup)
from ralph.util import presentation


class ReadOnlySelectWidget(forms.Select):
    def _has_changed(self, initial, data):
        return False

    def render(self, name, value, attrs=None, choices=()):
        labels = dict(self.choices)
        display = unicode(labels.get(value, ''))
        attr_class =  self.attrs.get('class', '')
        return mark_safe(
            '<div class="input uneditable-input %s">'
            '<input type="hidden" name="%s" value="%s">'
            '%s'
            '</div>' % (
                escape(attr_class),
                escape(name),
                escape(value),
                escape(display),
            ),
        )


class ReadOnlyPriceWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        try:
            value = int(round(value))
            value = '{:,.0f} {}'.format(value,
                                        settings.CURRENCY).replace(',', ' ')
        except (ValueError, TypeError):
            pass
        return mark_safe(
            '<div class="input uneditable-input currency">%s</div>' %
            escape(value))


class ReadOnlyMultipleChoiceWidget(FilteredSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        output_values = []
        choices = dict([x for x in self.choices])
        for v in value:
            output_values.append(choices.get(v,''))
        return mark_safe('<div class="input uneditable-input">%s</div>' %
                         escape(','.join(output_values)))


class ReadOnlyWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        attr_class =  escape(self.attrs.get('class', ''))
        return mark_safe('''
        <input type="hidden" name="%s" value="%s">
        <div class="input uneditable-input %s">%s</div></input>''' % (
            escape(name), escape(value), attr_class, escape(value)))


class ReadOnlyPreWidget(forms.Widget):
    def render(self, name, value, attrs=None, choices=()):
        return mark_safe('''
        <input type="hidden" name="%s" value="%s">
        <div class="input uneditable-input"><pre>%s</pre></div></input>''' % (
            escape(name), escape(value), escape(value)))


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
                '<input type="hidden" name="%s" value="">' % (escape(name),),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_model_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (escape(name),
                                                                escape(value)),
                '<div class="input uneditable-input">',
                '<a href="/admin/discovery/devicemodel/%s">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (dm.id,
                    presentation.get_device_model_icon(dm), escape(dm.name)),
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
                '<input type="hidden" name="%s" value="">' % (escape(name),),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (escape(name),
                                                                escape(value)),
                '<div class="input uneditable-input">',
                '<a href="%s">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (dev.id,
                    presentation.get_device_icon(dev), escape(dev.name)),
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
                '<input type="hidden" name="%s" value="">' % (escape(name),),
                '<div class="input uneditable-input">',
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    presentation.get_device_icon(None), 'None'),
                '</div>',
            ]
        else:
            output = [
                '<input type="hidden" name="%s" value="%s">' % (escape(name),
                                                                escape(value)),
                '<div class="input uneditable-input">',
                '<a href="/ui/racks/sn-%s/info/">'
                '<i class="fugue-icon %s"></i>&nbsp;%s</a>' % (
                    slugify(dev.sn),
                    presentation.get_device_icon(dev),
                    escape(dev.name),
                ),
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
                '<input type="checkbox" checked="checked" '
                'name="%s" value="%s">' % (name, value),
                '<a href="../../catalog/component/%s/%s">%s</a>' % (mg.type,
                                                                    mg.id,
                                                                    mg.name),
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
                '<input type="checkbox" checked="checked" '
                'name="%s" value="%s">' % (name, value),
                '<a href="../../catalog/device/%s/%s">%s</a>' % (mg.type,
                                                                 mg.id,
                                                                 mg.name),
                '</label>',
            ]
        return mark_safe('\n'.join(output))


class DateWidget(forms.DateInput):
    def render(self, name, value='', attrs=None, choices=()):
        if value == None:
            value = ''
        # TODO: make it generic and use self.build_attrs(attrs)
        attr_id = escape(attrs.get('id', "id_{}".format(name)))
        attr_class = escape(self.attrs.get('class', ''))
        attr_placeholder = escape(self.attrs.get('placeholder', ''))
        output = ('<input type="text" id="%s" name="%s" class="datepicker %s" '
                  'placeholder="%s" value="%s" data-date-format="yyyy-mm-dd">')
        return mark_safe(output % (attr_id, escape(name), attr_class,
                                   attr_placeholder, escape(value or '')))


class ReadOnlyDateWidget(forms.DateInput):
    def render(self, name, value, attrs=None, choices=()):
        formatted = escape(value) if value else ''
        return mark_safe('''
        <input type="hidden" name="%s" value="%s">
        <div>%s</div></input>''' % (
            escape(name), formatted, formatted))


class CurrencyWidget(forms.TextInput):
    def render(self, name, value=0, attrs=None, *args, **kwargs):
        value = '{}'.format(value)
        attrs['class'] = attrs.get('class', '') + ' currency'
        return super(CurrencyWidget, self).render(name, value, attrs,
                                                  *args, **kwargs)


class ButtonWidget(forms.Widget):
    def render(self, name, value='', attrs=None, choices=()):
        attr_class = escape(self.attrs.get('class', ''))
        attr_value = escape(self.attrs.get('value', ''))
        return mark_safe(
            '<button type="button" class="btn %s">%s</button>' % (
                attr_class, attr_value)
        )
