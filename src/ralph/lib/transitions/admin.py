# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

from ralph.lib.transitions.models import TransitionConfigModel


@register(TransitionConfigModel)
class TransitionConfigModelAdmin(RalphAdmin):
    list_display = [
        'name', 'field_name', 'content_type', 'source', 'target', 'actions'
    ]
