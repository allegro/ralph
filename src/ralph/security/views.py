# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.views.extra import RalphDetailView
from ralph.security.models import SecurityScan


class ScanStatusInChangeListMixin(object):
    def scan_status(self, obj):
        scans = SecurityScan.objects.filter(base_object_id=obj.id)
        if scans:
            scan = scans.latest("last_scan_date")
            if scan.is_ok:
                if scan.has_vulnerabilities():
                    icon_name, desc = "fa-times", _(
                        "Scan succeed. Found vulnerabilities: {}".format(
                            scan.vulnerabilities.count()
                        )
                    )
                else:
                    icon_name, desc = "fa-check", _(
                        "Scan succeed. Host is clean so far."
                    )
            else:
                icon_name, desc = "fa-exclamation", _(
                    "Scan failed.".format(
                        scan.vulnerabilities.count()
                    )
                )
            html = '<i title="{desc}" class="fa {icon_name}" aria-hidden="true"></i>'.format(  # noqa
                icon_name=icon_name,
                desc=desc,
            )
        else:
            html = '<span title="No scan so far">-</span>'
        return mark_safe(html)
    scan_status.short_description = _('Security scan')


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
