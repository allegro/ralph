# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

from ralph.tests.models import Car, Manufacturer


@register(Car)
class CarAdmin(RalphAdmin):
    ordering = ['name']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    ordering = ['name', '-country']
