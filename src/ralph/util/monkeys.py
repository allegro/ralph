#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ajax_select
from django import forms

from ajax_select import get_lookup
from django.forms.util import flatatt
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class PatchedAutoCompleteSelectWidget(forms.widgets.TextInput):

    """  widget to select a model and return it as text """

    add_link = None

    def __init__(self,
                 channel,
                 help_text=u'',
                 show_help_text=True,
                 plugin_options={},
                 *args, **kwargs):
        self.plugin_options = plugin_options
        self.add_link = plugin_options.get('add_link')
        super(forms.widgets.TextInput, self).__init__(*args, **kwargs)
        self.channel = channel
        self.help_text = help_text
        self.show_help_text = show_help_text

    def render(self, name, value, attrs=None):

        value = value or ''
        final_attrs = self.build_attrs(attrs)
        self.html_id = final_attrs.pop('id', name)

        current_repr = ''
        initial = None
        lookup = get_lookup(self.channel)
        if value:
            objs = lookup.get_objects([value])
            try:
                obj = objs[0]
            except IndexError:
                raise Exception("%s cannot find object:%s" % (lookup, value))
            current_repr = lookup.format_item_display(obj)
            initial=[current_repr, obj.pk]

        if self.show_help_text:
            help_text = self.help_text
        else:
            help_text = u''

        context = {
            'name': name,
            'html_id': self.html_id,
            'current_id': value,
            'current_repr': current_repr,
            'help_text': help_text,
            'extra_attrs': mark_safe(flatatt(final_attrs)),
            'func_slug': self.html_id.replace("-",""),
            'add_link': self.add_link,
        }
        context.update(plugin_options(lookup,self.channel,self.plugin_options,initial))
        context.update(bootstrap())

        return mark_safe(render_to_string(('autocompleteselect_%s.html' % self.channel, 'autocompleteselect.html'),context))

    def value_from_datadict(self, data, files, name):

        got = data.get(name, None)
        if got:
            return long(got)
        else:
            return None

    def id_for_label(self, id_):
        return '%s_text' % id_



ajax_select.AutoCompleteSelectWidget = PatchedAutoCompleteSelectWidget
