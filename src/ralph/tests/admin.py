# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.attachments.admin import AttachmentsMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.tests.models import Bar, Car, Car2, Foo, Manufacturer, Order


@register(Car)
class CarAdmin(RalphAdmin):
    ordering = ['name']
    list_filter = ['year']
    search_fields = ['name', 'foos__bar']


@register(Bar)
class BarAdmin(RalphAdmin):
    list_filter = ['date', 'name', 'created', 'price', 'count']


class BarsM2MInline(RalphTabularM2MInline):
    model = Bar
    fields = ('name', 'date', 'price', 'count')
    extra = 1
    verbose_name = _('Bars')


@register(Foo)
class FooAdmin(RalphAdmin):
    inlines = [BarsM2MInline]


@register(Car2)
class Car2Admin(RalphAdmin):
    list_filter = ['manufacturer']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    ordering = ['name', '-country']


@register(Order)
class OrderAdmin(AttachmentsMixin, TransitionAdminMixin, RalphAdmin):
    change_views = []
