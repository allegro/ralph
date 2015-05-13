# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.assets.models import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service
)


@admin.register(Service)
class ServiceAdmin(reversion.VersionAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerAdmin(reversion.VersionAdmin):
    pass


@admin.register(Environment)
class EnvironmentAdmin(reversion.VersionAdmin):
    pass


@admin.register(AssetModel)
class AssetModelAdmin(reversion.VersionAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(reversion.VersionAdmin):
    pass
