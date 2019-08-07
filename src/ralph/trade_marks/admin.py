# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import (
    custom_title_filter,
    DateListFilter,
    RelatedAutocompleteFieldListFilter
)
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.trade_marks.forms import IntellectualPropertyForm
from ralph.trade_marks.models import (
    ProviderAdditionalMarking,
    TradeMark,
    TradeMarkAdditionalCountry,
    TradeMarkCountry,
    TradeMarkRegistrarInstitution,
    TradeMarksLinkedDomains,
    TradeMarkType
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
        'registrant_number',
        'type',
        ('valid_from', DateListFilter),
        ('valid_to', DateListFilter),
        'additional_markings',
        'holder',
        'status',
        (
            'trademarkadditionalcountry__country',
            custom_title_filter('Region', RelatedAutocompleteFieldListFilter)
        )
    ]
    list_display = [
        'registrant_number', 'region', 'name', 'registrant_class',
        'valid_from', 'valid_to', 'status', 'holder', 'representation',
    ]
    raw_id_fields = [
        'business_owner', 'technical_owner', 'holder'
    ]
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'registrant_number', 'type', 'image', 'image_tag',
                'registrant_class', 'valid_from', 'valid_to',
                'registrar_institution', 'order_number_url',
                'additional_markings', 'holder', 'status', 'remarks'
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'business_owner', 'technical_owner'
            )
        })
    )

    def region(self, obj):
        return ', '.join(
            tm_country.country.name for tm_country in
            obj.trademarkadditionalcountry_set.all()
        )

    def representation(self, obj):
        if obj.image:
            return self.image_tag(obj)
        else:
            return TradeMarkType.desc_from_id(obj.type)

    representation.allow_tags = True

    def image_tag(self, obj):
        if not obj.image:
            return ""
        return mark_safe(
            '<img src="%s" width="150" />' % obj.image.url
        )

    image_tag.short_description = _('Image')
    image_tag.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'trademarkadditionalcountry_set__country'
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
