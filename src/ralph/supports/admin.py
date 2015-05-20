# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.supports.models import Support, SupportType


@register(Support)
class SupportAdmin(PermissionAdminMixin, RalphAdmin):
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


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):
    pass
