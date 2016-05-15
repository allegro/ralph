from django.contrib import admin

from .models import SomeModel
from ..admin import CustomFieldValueAdminMaxin

site = admin.AdminSite(name="cf_admin")


# @admin.register(SomeModel)
class SomeModelAdmin(CustomFieldValueAdminMaxin, admin.ModelAdmin):
    pass


site.register(SomeModel, SomeModelAdmin)
