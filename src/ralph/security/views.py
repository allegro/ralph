# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.views.extra import RalphDetailView
from ralph.security.models import Vulnerability


class ScanStatusInChangeListMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_select_related += ['securityscan', ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            vulnerabilities_count=Count('securityscan__vulnerabilities')
        )
        return qs

    def _to_span(self, css, text):
        return'<span class="{}">{}</span>'.format(css, text)

    def scan_status(self, obj):
        try:
            scan = obj.securityscan
        except ObjectDoesNotExist:
            html = self._to_span('', 'No scan')
        else:
            if scan.is_ok:
                if obj.vulnerabilities_count > 0:
                    html = self._to_span(
                        "alert", "Got vulnerabilities: {}".format(
                            obj.vulnerabilities_count
                        )
                    )
                else:
                    html = self._to_span("success", "Host clean")
            else:
                html = self._to_span("warning", "Scan failed")
        return mark_safe(html)
    scan_status.short_description = _('Security scan')


@register(Vulnerability)
class Vulnerability(RalphAdmin):
    search_fields = ['name', ]


class SecurityInfo(RalphDetailView):

    icon = 'lock'
    label = 'Security Info'
    name = 'security_info'
    url_name = None
    template_name = 'security/securityinfo/security_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            scan = self.object.securityscan
        except ObjectDoesNotExist:
            scan = None
        context['security_scan'] = scan
        return context
