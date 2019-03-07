# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import DateListFilter
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.trade_marks.forms import IntellectualPropertyForm
from ralph.trade_marks.models import (
    ProviderAdditionalMarking,
    TradeMark,
    TradeMarkAdditionalCountry,
    TradeMarkCountry,
    TradeMarkRegistrarInstitution,
    TradeMarksLinkedDomains
)


class TradeMarksLinkedView(RalphDetailViewAdmin):
    icon = 'table'
    name = 'table'
    label = _('Assigned to domain')
    url_name = 'assigned-to-domain'

    class TradeMarksLinkedInline(RalphTabularInline):
        model = TradeMarksLinkedDomains
        raw_id_fields = ('domain', admin.RelatedFieldListFilter)
        extra = 1

    inlines = [TradeMarksLinkedInline]


@register(TradeMark)
class TradeMarkAdmin(AttachmentsMixin, RalphAdmin):

    change_views = [TradeMarksLinkedView]
    form = IntellectualPropertyForm
    search_fields = ['name', 'id', ]
    readonly_fields = ['image_tag']
    list_select_related = [
        'technical_owner', 'business_owner', 'holder',
    ]
    list_filter = [
        'registrant_number', 'type',
        ('valid_to', DateListFilter), 'additional_markings',
        'holder', 'status'
    ]
    list_display = [
        'id', 'name', 'registrant_number', 'type',
        'valid_to', 'holder', 'status', 'image_tag'
    ]
    raw_id_fields = [
        'business_owner', 'technical_owner', 'holder'
    ]
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'registrant_number', 'type', 'image', 'image_tag',
                'registrant_class', 'valid_to', 'registrar_institution',
                'order_number_url', 'additional_markings',
                'holder', 'status', 'remarks'
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'business_owner', 'technical_owner'
            )
        })
    )

    class TradeMarksAdditionalCountryInline(RalphTabularInline):
        model = TradeMarkAdditionalCountry
        extra = 1
        verbose_name = _('country')

    inlines = [TradeMarksAdditionalCountryInline]


@register(ProviderAdditionalMarking)
class ProviderAdditionalMarkingAdmin(RalphAdmin):
    pass


@register(TradeMarkRegistrarInstitution)
class TradeMarkRegistrarInstitutionAdmin(RalphAdmin):

    search_fields = ['name']


@register(TradeMarkCountry)
class TradeMarkCountryAdmin(RalphAdmin):
    pass
