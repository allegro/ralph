# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import reversion

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.supports.models import Support, SupportType


@admin.register(Support)
class SupportAdmin(PermissionAdminMixin, reversion.VersionAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'contract_id',
            )
        }),
        (_('Additional info'), {
            'fields': (
                'date_from', 'date_to', 'producer',
                'support_type',
            )
        }),
    )


@admin.register(SupportType)
class SupportTypeAdmin(reversion.VersionAdmin):
    pass
