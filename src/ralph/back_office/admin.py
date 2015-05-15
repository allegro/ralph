# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

from ralph.back_office.models import (
    BackOfficeAsset,
    Warehouse
)

from django.views.generic import View


class ByServiceView(View):
    label = 'Dupa'
    url_name = 'by_service'


class DupaView(View):
    label = 'Dupa 2'
    url_name = 'by_service2'


@register(Warehouse)
class WarehousAdmin(RalphAdmin):
    extra_views = [ByServiceView, DupaView]
