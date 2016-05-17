from django.contrib import admin

from ..admin import CustomFieldValueAdminMaxin
from .models import SomeModel

site = admin.AdminSite(name="cf_admin")


# @admin.register(SomeModel)
class SomeModelAdmin(CustomFieldValueAdminMaxin, admin.ModelAdmin):
    pass


site.register(SomeModel, SomeModelAdmin)
