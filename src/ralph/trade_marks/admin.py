# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import (
    ChoicesListFilter,
    custom_title_filter,
    DateListFilter,
    RelatedAutocompleteFieldListFilter
)
from ralph.admin.mixins import RalphAdmin, RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.trade_marks.forms import (
    DesignForm,
    PatentForm,
    TradeMarkForm,
    UtilityModelForm
)
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
    TradeMarkKind,
    TradeMarkRegistrarInstitution,
    TradeMarksLinkedDomains,
    UtilityModel,
    UtilityModelAdditionalCountry,
    UtilityModelLinkedDomains
)


class IntellectualPropertyLinkedDomainViewBase(RalphDetailViewAdmin):
    icon = "table"
    name = "table"
    label = _("Assigned to domain")
    url_name = "assigned-to-domain"


class TradeMarksLinkedDomainsView(IntellectualPropertyLinkedDomainViewBase):
    class Inline(RalphTabularInline):
        model = TradeMarksLinkedDomains
        raw_id_fields = ("domain", admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class DesignLinkedDomainsView(IntellectualPropertyLinkedDomainViewBase):
    class Inline(RalphTabularInline):
        model = DesignsLinkedDomains
        raw_id_fields = ("domain", admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class PatentLinkedDomainsView(IntellectualPropertyLinkedDomainViewBase):
    class Inline(RalphTabularInline):
        model = PatentsLinkedDomains
        raw_id_fields = ("domain", admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class UtilityModelLinkedDomainsView(IntellectualPropertyLinkedDomainViewBase):
    class Inline(RalphTabularInline):
        model = UtilityModelLinkedDomains
        raw_id_fields = ("domain", admin.RelatedFieldListFilter)
        extra = 1

    inlines = [Inline]


class IntellectualPropertyAdminBase(AttachmentsMixin, RalphAdmin):
    search_fields = [
        "name",
        "id",
    ]
    readonly_fields = ["image_tag"]
    list_select_related = [
        "technical_owner",
        "business_owner",
        "holder",
    ]
    list_filter = [
        "number",
        ("valid_from", DateListFilter),
        ("valid_to", DateListFilter),
        "additional_markings",
        "holder",
        "status",
    ]
    list_display = [
        "number",
        "region",
        "name",
        "classes",
        "valid_from",
        "valid_to",
        "status",
        "holder",
        "representation",
        "get_database_link",
    ]
    raw_id_fields = ["business_owner", "technical_owner", "holder"]
    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "database_link",
                    "number",
                    "image",
                    "image_tag",
                    "classes",
                    "valid_from",
                    "valid_to",
                    "registrar_institution",
                    "order_number_url",
                    "additional_markings",
                    "holder",
                    "status",
                    "remarks",
                )
            },
        ),
        (_("Ownership info"), {"fields": ("business_owner", "technical_owner")}),
    )

    def get_database_link(self, obj):
        if obj.database_link:
            return mark_safe(
                '<a target="_blank" href="{}">link</a>'.format(obj.database_link)
            )
        else:
            return "-"

    get_database_link.short_description = _("Database link")

    def representation(self, obj):
        if obj.image:
            return self.image_tag(obj)
        else:
            return "-"

    def image_tag(self, obj):
        if not obj.image:
            return ""
        return mark_safe('<img src="{}" width="150" />'.format(obj.image.url))

    image_tag.short_description = _("Image")


@register(TradeMark)
class TradeMarkAdmin(IntellectualPropertyAdminBase):
    class TypeFilter(ChoicesListFilter):
        title = "Trade Mark type"
        parameter_name = "type"

        @property
        def _choices_list(self):
            try:
                return [(t.id, t.type) for t in TradeMarkKind.objects.all()]
            except:  # noqa
                return []

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(type__id=self.value())
            else:
                return queryset

    change_views = [TradeMarksLinkedDomainsView]
    form = TradeMarkForm
    list_filter = [
        "number",
        ("type", TypeFilter),
        ("valid_from", DateListFilter),
        ("valid_to", DateListFilter),
        "additional_markings",
        "holder",
        "status",
        (
            "trademarkadditionalcountry__country",
            custom_title_filter("Region", RelatedAutocompleteFieldListFilter),
        ),
    ]

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "database_link",
                    "number",
                    "type",
                    "image",
                    "image_tag",
                    "classes",
                    "valid_from",
                    "valid_to",
                    "registrar_institution",
                    "order_number_url",
                    "additional_markings",
                    "holder",
                    "status",
                    "remarks",
                )
            },
        ),
        (_("Ownership info"), {"fields": ("business_owner", "technical_owner")}),
    )

    def region(self, obj):
        return ", ".join(
            tm_country.country.name
            for tm_country in obj.trademarkadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("trademarkadditionalcountry_set__country")
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = TradeMarkAdditionalCountry
        extra = 1
        verbose_name = _("country")

    inlines = [AdditionalCountryInline]


@register(Design)
class DesignAdmin(IntellectualPropertyAdminBase):
    change_views = [DesignLinkedDomainsView]
    form = DesignForm
    list_filter = [
        "number",
        ("valid_from", DateListFilter),
        ("valid_to", DateListFilter),
        "additional_markings",
        "holder",
        "status",
        (
            "designadditionalcountry__country",
            custom_title_filter("Region", RelatedAutocompleteFieldListFilter),
        ),
    ]

    def region(self, obj):
        return ", ".join(
            tm_country.country.name
            for tm_country in obj.designadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("designadditionalcountry_set__country")
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = DesignAdditionalCountry
        extra = 1
        verbose_name = _("country")

    inlines = [AdditionalCountryInline]


@register(Patent)
class PatentAdmin(IntellectualPropertyAdminBase):
    change_views = [PatentLinkedDomainsView]
    form = PatentForm
    list_filter = [
        "number",
        ("valid_from", DateListFilter),
        ("valid_to", DateListFilter),
        "additional_markings",
        "holder",
        "status",
        (
            "patentadditionalcountry__country",
            custom_title_filter("Region", RelatedAutocompleteFieldListFilter),
        ),
    ]

    def region(self, obj):
        return ", ".join(
            tm_country.country.name
            for tm_country in obj.patentadditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("patentadditionalcountry_set__country")
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = PatentAdditionalCountry
        extra = 1
        verbose_name = _("country")

    inlines = [AdditionalCountryInline]


@register(ProviderAdditionalMarking)
class ProviderAdditionalMarkingAdmin(RalphAdmin):
    pass


@register(TradeMarkRegistrarInstitution)
class TradeMarkRegistrarInstitutionAdmin(RalphAdmin):
    search_fields = ["name"]


@register(TradeMarkCountry)
class TradeMarkCountryAdmin(RalphAdmin):
    pass


@register(UtilityModel)
class UtilityModelAdmin(IntellectualPropertyAdminBase):
    change_views = [UtilityModelLinkedDomainsView]
    form = UtilityModelForm
    list_filter = [
        "number",
        ("valid_from", DateListFilter),
        ("valid_to", DateListFilter),
        "additional_markings",
        "holder",
        "status",
        (
            "utilitymodeladditionalcountry__country",
            custom_title_filter("Region", RelatedAutocompleteFieldListFilter),
        ),
    ]

    def region(self, obj):
        return ", ".join(
            tm_country.country.name
            for tm_country in obj.utilitymodeladditionalcountry_set.all()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("utilitymodeladditionalcountry_set__country")
        )

    class AdditionalCountryInline(RalphTabularInline):
        model = UtilityModelAdditionalCountry
        extra = 1
        verbose_name = _("country")

    inlines = [AdditionalCountryInline]
