# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.tests.models import Car, Manufacturer, Order


@register(Car)
class CarAdmin(RalphAdmin):
    ordering = ['name']
    list_filter = ['year']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    ordering = ['name', '-country']


@register(Order)
class OrderAdmin(TransitionAdminMixin, RalphAdmin):
    pass
