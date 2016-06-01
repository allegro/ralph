from django.contrib import admin

from ..admin import CustomFieldValueAdminMixin
from .models import SomeModel

site = admin.AdminSite(name="cf_admin")


@admin.register(SomeModel)
class SomeModelAdmin(CustomFieldValueAdminMixin, admin.ModelAdmin):
    pass


site.register(SomeModel, SomeModelAdmin)
