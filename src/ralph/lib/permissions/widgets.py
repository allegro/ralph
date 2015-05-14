# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.forms import Field, HiddenInput


class ReadOnlyWidget(HiddenInput):
    is_hidden = False

    def render(self, name, value, attrs=None):
        html = super(ReadOnlyWidget, self).render(name, value, attrs)
        wrapped_value = '<div class="empty">{}</div>'.format(value or 'empty')
        return wrapped_value + html


class ReadOnlyField(Field):

    def __init__(self, *args, **kwargs):
        kwargs['widget'] = ReadOnlyWidget
        super(ReadOnlyField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return value or None
