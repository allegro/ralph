# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service
)
from ralph.assets.models.components import (
    ComponentModel,
    GenericComponent
)
from ralph.data_importer import resources


@admin.register(Service)
class ServiceAdmin(reversion.VersionAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerAdmin(ImportExportModelAdmin, reversion.VersionAdmin):
    pass


@admin.register(Environment)
class EnvironmentAdmin(reversion.VersionAdmin):
    pass


@admin.register(AssetModel)
class AssetModelAdmin(ImportExportModelAdmin, reversion.VersionAdmin):
    resource_class = resources.AssetModelResource


@admin.register(Category)
class CategoryAdmin(reversion.VersionAdmin):
    pass


@admin.register(ComponentModel)
class ComponentModelAdmin(reversion.VersionAdmin):
    pass


@admin.register(GenericComponent)
class GenericComponentAdmin(reversion.VersionAdmin):
    pass
