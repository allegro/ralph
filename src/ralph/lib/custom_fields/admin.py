# -*- coding: utf-8 -*-
from django import forms
from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from ralph.admin import RalphAdmin, register
from ralph.admin.mixins import RalphGenericTabularInline
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue


class CustomFieldFormfieldView(View):
    """
    Return HTML for custom field formfield.
    """

    http_method_names = ['get']

    def get(self, request, custom_field_id, *args, **kwargs):
        custom_field = get_object_or_404(CustomField, pk=custom_field_id)
        form_field = custom_field.get_form_field()
        return HttpResponse(form_field.widget.render(
            name='__empty__',
            value=form_field.initial
        ))


@register(CustomField)
class CustomFieldAdmin(RalphAdmin):
    list_display = ['name', 'attribute_name', 'type', 'default_value']
    search_fields = ['name', 'attribute_name']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url(
                r'^(?P<custom_field_id>\d+)/formfield/$',
                CustomFieldFormfieldView.as_view(),
                name='customfield_formfield'
            ),
        ]
        return my_urls + urls


class CustomFieldValueForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.custom_field_id:
            self.fields['value'] = self.instance.custom_field.get_form_field()


class CustomFieldValueInline(RalphGenericTabularInline):
    model = CustomFieldValue
    form = CustomFieldValueForm
    raw_id_fields = ['custom_field']
    template = 'custom_fields/edit_inline/tabular.html'


class CustomFieldValueAdminMaxin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = list(self.inlines) + [CustomFieldValueInline]
