# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.supports.models import Support


@admin.register(Support)
class SupportAdmin(reversion.VersionAdmin):
    pass
