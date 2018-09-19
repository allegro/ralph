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
        'valid_to', 'holder', 'status'
    ]
    raw_id_fields = [
        'business_owner', 'technical_owner', 'holder'
    ]
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'registrant_number', 'type',
                'registrant_class', 'date_to', 'region',
                'order_number_url', 'additional_markings', 'holder',
                'status', 'remarks'
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'business_owner', 'technical_owner'
            )
        })
    )
    search_fields = ['name', 'id', ]


@register(ProviderAdditionalMarking)
class ProviderAdditionalMarkingAdmin(RalphAdmin):
    pass
