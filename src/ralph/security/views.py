# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.views.extra import RalphDetailView


class ScanStatusInChangeListMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_select_related += ['securityscan', ]

    def scan_status(self, obj):
        try:
            scan = obj.securityscan
        except ObjectDoesNotExist:
            html = '<span title="No scan so far">-</span>'
        else:
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
