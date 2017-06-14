import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import NoReverseMatch
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import custom_title_filter
from ralph.admin.helpers import get_admin_url
from ralph.admin.views.extra import RalphDetailView
from ralph.configuration_management.models import SCMScanStatus
# NOTE(romcheg): These functions could be moved to a common place
from ralph.security.views import _linkify, _url_name_for_change_view


logger = logging.getLogger(__name__)


class SCMScanInfo(RalphDetailView):

    icon = 'cogs'
    label = 'SCM info'
    name = 'scm_info'
    url_name = None
    template_name = 'configuration_management/scminfo/scm_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            scan = self.object.scmscan
        except ObjectDoesNotExist:
            scan = None
        context['scm_scan'] = scan

        hostname = getattr(self.object, 'hostname', None)

        if hostname:
            context['scm_tool_url'] = settings.SCM_TOOL_URL.format(
                hostname=hostname
            )

        return context


class SCMScanStatusInChangeListMixin(object):

    icon_no_scan = '-'
    icon_scan_ok = '<i class="fa fa-check-circle" aria-hidden="true"></i>'
    icon_scan_error = ('<i class="fa fa-exclamation-triangle" '
                       'aria-hidden="true"></i>')
    icon_scan_fail = '<i class="fa fa-question-circle" aria-hidden="true"></i>'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_select_related += ['scmscan', ]
        self.list_filter += [
            (
                'scmscan__scan_status',
                custom_title_filter('SCM scan status')
            ),
            (
                'scmscan__last_scan_date',
                custom_title_filter('Last SCM scan date')
            )
        ]

    def _to_span(self, css, text):
        return'<span class="{}">{}</span>'.format(css, text)

    def scm_scan_status(self, obj):
        try:
            scan = obj.scmscan
        except ObjectDoesNotExist:
            html = self._to_span('', self.icon_no_scan)
        else:
            if scan.scan_status == SCMScanStatus.ok:
                html = self._to_span("success", self.icon_scan_ok)
            elif scan.scan_status == SCMScanStatus.error:
                    html = self._to_span("alert", self.icon_scan_error)
            else:
                html = self._to_span("warning", self.icon_scan_fail)

            url_name = _url_name_for_change_view(type(obj), 'scm_info')

            if not url_name:
                logger.error("No scm info view for obj of type: {}".format(
                    type(obj))
                )
            else:
                try:
                    url = get_admin_url(obj, url_name)
                    html = _linkify(html, url)
                except NoReverseMatch:
                    logger.error(
                        "cant reverse url for: {}, {}".format(obj, url_name)
                    )
        return mark_safe(html)
    scm_scan_status.short_description = _('SCM scan')
