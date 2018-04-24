# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.filters import DateListFilter
from ralph.attachments.admin import AttachmentsMixin
from ralph.ssl_certificates.models import SSLCertificate


@register(SSLCertificate)
class SSLCertificateAdmin(AttachmentsMixin, RalphAdmin):
    list_select_related = [
        'technical_owner', 'business_owner',
        'certificate_issued_by'
    ]

    list_filter = [
        'certificate', 'certificate_type', 'business_owner',
        'technical_owner', ('date_from', DateListFilter),
        ('date_to', DateListFilter), 'certificate_issued_by',
    ]

    list_display = [
        'certificate', 'business_owner',
        'technical_owner', 'certificate_issued_by',
        'date_from', 'date_to'
    ]

    raw_id_fields = [
        'business_owner',
        'technical_owner', 'certificate_issued_by'
    ]

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'certificate', 'certificate_type',
                'certificate_issued_by', 'san',
                'price', 'date_from', 'date_to',
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'business_owner', 'technical_owner'
            )
        })
    )
    search_fields = ['certificate', ]
