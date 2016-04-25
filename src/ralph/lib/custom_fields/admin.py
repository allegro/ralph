# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
from ralph.admin.mixins import RalphGenericTabularInline
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue


@register(CustomField)
class CustomFieldAdmin(RalphAdmin):
    list_display = ['name', 'attribute_name', 'type', 'default_value']
    search_fields = ['name', 'attribute_name']


class CustomFieldValueInline(RalphGenericTabularInline):
    model = CustomFieldValue
    raw_id_fields = ['custom_field']


class CustomFieldValueAdminMaxin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = list(self.inlines) + [CustomFieldValueInline]
