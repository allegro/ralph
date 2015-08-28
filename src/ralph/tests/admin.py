# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
from ralph.admin.filters import TextFilter
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.tests.models import Car, Manufacturer, Order


class NameFilter(TextFilter):
    title = 'name'
    parameter_name = 'name'


@register(Car)
class CarAdmin(RalphAdmin):
    ordering = ['name']
    list_filter = ['year', NameFilter]


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    ordering = ['name', '-country']


@register(Order)
class OrderAdmin(TransitionAdminMixin, RalphAdmin):
    pass
