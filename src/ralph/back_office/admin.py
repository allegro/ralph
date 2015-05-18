# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

from ralph.back_office.models import (
    Warehouse
)

from django.views.generic import View


class ByServiceView(View):
    label = 'Extra'
    url_name = 'by_service'


class ExtraView(View):
    label = 'Test'
    url_name = 'by_service2'


@register(Warehouse)
class WarehousAdmin(RalphAdmin):
    extra_views = [ByServiceView, ExtraView]
