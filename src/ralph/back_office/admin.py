# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

from ralph.back_office.models import Warehouse

from django.views.generic import View


class ExtraView(View):
    label = 'Extra view'
    url_name = 'extra_view'


@register(Warehouse)
class WarehousAdmin(RalphAdmin):

    extra_views = [ExtraView]
