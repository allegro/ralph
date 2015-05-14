# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.forms import Field, Widget


class ReadOnlyWidget(Widget):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        return """<div class="empty">{}</div>
        <p class="help">You don\'t have permission for edit this field.</p>
        """.format(value or '-')


class ReadOnlyField(Field):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = ReadOnlyWidget()
        super(ReadOnlyField, self).__init__(*args, **kwargs)
