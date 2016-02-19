# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer.resources import DomainResource
from ralph.domains.models.domains import (
    Domain,
    DomainContract,
    DomainRegistrant
)


class DomainContractInline(RalphTabularInline):
    model = DomainContract
    extra = 0


@register(Domain)
class DomainAdmin(AttachmentsMixin, RalphAdmin):
    resource_class = DomainResource
    list_select_related = ['technical_owner', 'business_owner', 'domain_holder']
    list_filter = [
        'name', 'service_env',
    ]
    list_display = [
        'name', 'parent', 'business_owner',
        'technical_owner', 'domain_holder'
    ]
    raw_id_fields = [
        'service_env', 'business_owner', 'technical_owner', 'domain_holder'
    ]
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'remarks', 'domain_status',
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'service_env',
                'business_segment', 'business_owner',
                'technical_owner', 'domain_holder'
            )
        })
    )
    search_fields = ['name', ]
    inlines = (DomainContractInline, )


@register(DomainContract)
class DomainContractAdmin(AttachmentsMixin, RalphAdmin):
    list_select_related = ['domain', 'domain__service_env']
    list_filter = [
        'domain__name', 'domain__service_env__service__name'
    ]
    list_display = [
        'domain', 'expiration_date', 'price'
    ]
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'domain', 'expiration_date', 'registrant'

            )
        }),
        (_('Financial info'), {
            'fields': (
                'price',
            )
        }),
    )
    search_fields = ['domain__name', ]


@register(DomainRegistrant)
class DomainRegistrantAdmin(RalphAdmin):
    pass
