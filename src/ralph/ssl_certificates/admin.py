from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.filters import DateListFilter
from ralph.attachments.admin import AttachmentsMixin
from ralph.ssl_certificates.models import SSLCertificate


@register(SSLCertificate)
class SSLCertificateAdmin(AttachmentsMixin, RalphAdmin):
    list_select_related = [
        'issued_by',
    ]

    list_filter = [
        'name', 'certificate_type',
        ('date_from', DateListFilter),
        ('date_to', DateListFilter), 'issued_by',
        'service_env',
    ]

    list_display = [
        'name', 'domain_ssl', 'issued_by',
        'date_from', 'date_to',
    ]

    raw_id_fields = [
        'issued_by', 'service_env',
    ]

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'domain_ssl', 'certificate_type',
                'issued_by', 'san',
                'price', 'date_from', 'date_to',
            )
        }),
        (_('Ownership info'), {
            'fields': (
                'service_env',
            )
        })
    )
    search_fields = ['name', ]
