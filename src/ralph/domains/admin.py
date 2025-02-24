# -*- coding: utf-8 -*-
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import DateListFilter
from ralph.admin.mixins import RalphAdmin, RalphTabularInline
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer.resources import DomainContractResource, DomainResource
from ralph.domains.forms import DomainContractForm, DomainForm
from ralph.domains.models.domains import (
    DNSProvider,
    Domain,
    DomainCategory,
    DomainContract,
    DomainProviderAdditionalServices,
    DomainRegistrant
)


class DomainContractInline(RalphTabularInline):
    model = DomainContract
    extra = 0


@register(Domain)
class DomainAdmin(AttachmentsMixin, RalphAdmin):
    form = DomainForm
    resource_class = DomainResource
    list_select_related = [
        "technical_owner",
        "business_owner",
        "domain_holder",
    ]
    list_filter = [
        "name",
        "service_env",
        "domain_status",
        "business_segment",
        "domain_holder",
        ("domaincontract__expiration_date", DateListFilter),
        "website_type",
        "website_url",
        "dns_provider",
        "domain_category",
        "domain_type",
        "additional_services",
    ]
    list_display = [
        "name",
        "business_owner",
        "technical_owner",
        "domain_holder",
        "service_env",
        "expiration_date",
    ]
    raw_id_fields = [
        "service_env",
        "business_owner",
        "technical_owner",
        "domain_holder",
    ]
    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "remarks",
                    "domain_status",
                    "website_type",
                    "website_url",
                    "domain_category",
                    "domain_type",
                    "dns_provider",
                    "additional_services",
                )
            },
        ),
        (
            _("Ownership info"),
            {
                "fields": (
                    "service_env",
                    "business_segment",
                    "business_owner",
                    "technical_owner",
                    "domain_holder",
                )
            },
        ),
    )
    search_fields = [
        "name",
    ]
    inlines = (DomainContractInline,)

    def expiration_date(self, obj):
        links = []
        for contract in obj.domaincontract_set.all():
            link = '<a href="{}">{} ({})</a>'.format(
                contract.get_absolute_url(),
                contract.expiration_date,
                contract.registrant or "-",
            )
            links.append(link)
        return format_html("<br>".join(links))

    expiration_date.short_description = "Expiration date"


@register(DomainContract)
class DomainContractAdmin(AttachmentsMixin, RalphAdmin):
    form = DomainContractForm
    resource_class = DomainContractResource
    list_select_related = ["domain", "domain__service_env"]
    list_filter = ["domain__name", "domain__service_env__service__name"]
    list_display = ["domain", "expiration_date", "price"]
    fieldsets = (
        (_("Basic info"), {"fields": ("domain", "expiration_date", "registrant")}),
        (_("Financial info"), {"fields": ("price",)}),
    )
    search_fields = [
        "domain__name",
    ]


@register(DomainProviderAdditionalServices)
class DomainProviderAdditionalServicesAdmin(RalphAdmin):
    pass


@register(DomainRegistrant)
class DomainRegistrantAdmin(RalphAdmin):
    pass


@register(DomainCategory)
class DomainCategory(RalphAdmin):
    pass


@register(DNSProvider)
class DNSProviderAdmin(RalphAdmin):
    pass
