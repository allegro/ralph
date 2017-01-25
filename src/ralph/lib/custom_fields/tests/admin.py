from django.contrib import admin

from ..admin import CustomFieldValueAdminMixin
from .models import ModelA, ModelB, SomeModel

site = admin.AdminSite(name="cf_admin")


@admin.register(SomeModel)
class SomeModelAdmin(CustomFieldValueAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ModelA)
class ModelAAdmin(CustomFieldValueAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ModelB)
class ModelBAdmin(CustomFieldValueAdminMixin, admin.ModelAdmin):
    pass


site.register(SomeModel, SomeModelAdmin)
site.register(ModelA, ModelAAdmin)
site.register(ModelB, ModelBAdmin)
