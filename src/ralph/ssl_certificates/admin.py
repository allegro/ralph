from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import DateListFilter
from ralph.admin.mixins import RalphAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.ssl_certificates.forms import SSLCertificateForm
from ralph.ssl_certificates.models import SSLCertificate


@register(SSLCertificate)
class SSLCertificateAdmin(AttachmentsMixin, RalphAdmin):
    form = SSLCertificateForm
    list_select_related = [
        "issued_by",
    ]

    list_filter = [
        "name",
        "certificate_type",
        ("date_from", DateListFilter),
        ("date_to", DateListFilter),
        "issued_by",
        "service_env",
        "certificate_repository",
    ]

    list_display = [
        "name",
        "domain_ssl",
        "issued_by",
        "date_from",
        "date_to",
        "certificate_repository",
    ]

    raw_id_fields = [
        "issued_by",
        "service_env",
    ]

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "domain_ssl",
                    "certificate_type",
                    "issued_by",
                    "san",
                    "price",
                    "date_from",
                    "date_to",
                    "certificate_repository",
                )
            },
        ),
        (_("Ownership info"), {"fields": ("service_env",)}),
    )
    search_fields = [
        "name",
    ]
