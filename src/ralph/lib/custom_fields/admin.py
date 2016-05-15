# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.admin import RalphAdmin, register
from ralph.admin.mixins import RalphGenericTabularInline
from ralph.lib.custom_fields.forms import (
    CustomFieldValueForm,
    CustomFieldValueFormSet
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue
from ralph.lib.custom_fields.views import CustomFieldFormfieldView


@register(CustomField)
class CustomFieldAdmin(RalphAdmin):
    list_display = ['name', 'attribute_name', 'type', 'default_value']
    search_fields = ['name', 'attribute_name']

    def get_urls(self):
        """
        Expose extra "<custom_field>/formfield" url for returning custom field
        formfield html.
        """
        urls = super().get_urls()
        my_urls = [
            url(
                r'^(?P<custom_field_id>.+)/formfield/$',
                CustomFieldFormfieldView.as_view(),
                name='customfield_formfield'
            ),
        ]
        return my_urls + urls


class CustomFieldValueInline(RalphGenericTabularInline):
    model = CustomFieldValue
    form = CustomFieldValueForm
    formset = CustomFieldValueFormSet
    raw_id_fields = ['custom_field']
    template = 'custom_fields/edit_inline/tabular.html'


class CustomFieldValueAdminMaxin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = list(self.inlines) + [CustomFieldValueInline]
