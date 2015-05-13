# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.backoffice.models import (
    BackOfficeAsset,
    Warehouse
)


@admin.register(BackOfficeAsset)
class BackOfficeAssetAdmin(reversion.VersionAdmin):
    pass


@admin.register(Warehouse)
class WarehousAdmin(reversion.VersionAdmin):
    pass