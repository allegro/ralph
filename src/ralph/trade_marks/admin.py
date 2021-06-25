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
from ralph.trade_marks.forms import DesignForm, PatentForm, TradeMarkForm
from ralph.trade_marks.models import (
    Design,
    DesignAdditionalCountry,
    DesignsLinkedDomains,
    Patent,
    PatentAdditionalCountry,
    PatentsLinkedDomains,
    ProviderAdditionalMarking,
    TradeMark,
    TradeMarkAdditionalCountry,
    TradeMarkCountry,
    TradeMarkRegistrarInstitution,
    TradeMarksLinkedDomains,
    TradeMarkType
)


class IntellectualPropertyLinkedDomainVeiwBase(RalphDetailViewAdmin):
    icon = 'table'
    name = 'table'
    label = _('Assigned to domain')
    url_name = 'assigned-to-domain'


class TradeMarksLinkedDomainsView(IntellectualPropertyLinkedDomainVeiwBase):

    class Inline(RalphTabularInline):
        model = TradeMarksLinkedDomains
        raw_id_fields = ('domain', admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class DesignLinkedDomainsView(IntellectualPropertyLinkedDomainVeiwBase):

    class Inline(RalphTabularInline):
        model = DesignsLinkedDomains
        raw_id_fields = ('domain', admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class PatentLinkedDomainsView(IntellectualPropertyLinkedDomainVeiwBase):

    class Inline(RalphTabularInline):
        model = PatentsLinkedDomains
        raw_id_fields = ('domain', admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class IntellectualPropertyAdminBase(AttachmentsMixin, RalphAdmin):

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


@register(TradeMark)
class TradeMarkAdmin(IntellectualPropertyAdminBase):

    change_views = [TradeMarksLinkedDomainsView]
    form = TradeMarkForm
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

    def region(self, obj):
        return ', '.join(
            tm_country.country.name for tm_country in
            obj.trademarkadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'trademarkadditionalcountry_set__country'
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = TradeMarkAdditionalCountry
        extra = 1
        verbose_name = _('country')

    inlines = [AdditionalCountryInline]


@register(Design)
class DesignAdmin(IntellectualPropertyAdminBase):

    change_views = [DesignLinkedDomainsView]
    form = DesignForm
    list_filter = [
        'registrant_number',
        'type',
        ('valid_from', DateListFilter),
        ('valid_to', DateListFilter),
        'additional_markings',
        'holder',
        'status',
        (
            'designadditionalcountry__country',
            custom_title_filter('Region', RelatedAutocompleteFieldListFilter)
        )
    ]

    def region(self, obj):
        return ', '.join(
            tm_country.country.name for tm_country in
            obj.designadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'designadditionalcountry_set__country'
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = DesignAdditionalCountry
        extra = 1
        verbose_name = _('country')

    inlines = [AdditionalCountryInline]


@register(Patent)
class PatentAdmin(IntellectualPropertyAdminBase):
    change_views = [PatentLinkedDomainsView]
    form = PatentForm
    list_filter = [
        'registrant_number',
        'type',
        ('valid_from', DateListFilter),
        ('valid_to', DateListFilter),
        'additional_markings',
        'holder',
        'status',
        (
            'patentadditionalcountry__country',
            custom_title_filter('Region', RelatedAutocompleteFieldListFilter)
        )
    ]

    def region(self, obj):
        return ', '.join(
            tm_country.country.name for tm_country in
            obj.patentadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'patentadditionalcountry_set__country'
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = PatentAdditionalCountry
        extra = 1
        verbose_name = _('country')

    inlines = [AdditionalCountryInline]


@register(ProviderAdditionalMarking)
class ProviderAdditionalMarkingAdmin(RalphAdmin):
    pass


@register(TradeMarkRegistrarInstitution)
class TradeMarkRegistrarInstitutionAdmin(RalphAdmin):

    search_fields = ['name']


@register(TradeMarkCountry)
class TradeMarkCountryAdmin(RalphAdmin):
    pass
