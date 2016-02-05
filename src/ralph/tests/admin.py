# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
from ralph.attachments.admin import AttachmentsMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.tests.models import Bar, Car, Car2, Manufacturer, Order


@register(Car)
class CarAdmin(RalphAdmin):
    ordering = ['name']
    list_filter = ['year']


@register(Bar)
class BarAdmin(RalphAdmin):
    list_filter = ['date', 'name', 'created', 'price', 'count']


@register(Car2)
class Car2Admin(RalphAdmin):
    list_filter = ['manufacturer']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    ordering = ['name', '-country']


@register(Order)
class OrderAdmin(AttachmentsMixin, TransitionAdminMixin, RalphAdmin):
    change_views = []
