# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms

from django.contrib.admin.templatetags.admin_static import static


class AdminDateWidget(forms.DateInput):
    @property
    def media(self):
        js = ['foundation-datepicker.js']
        return forms.Media(js=[static('js/%s' % path) for path in js])

    def render(self, name, value, attrs=None):
        attrs['class'] = 'datepicker'
        return super(AdminDateWidget, self).render(name, value, attrs=attrs)
