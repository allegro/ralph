import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import NoReverseMatch
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import custom_title_filter
from ralph.admin.helpers import get_admin_url
from ralph.admin.views.extra import RalphDetailView
from ralph.configuration_management.models import SCMCheckResult
# NOTE(romcheg): These functions could be moved to a common place
from ralph.security.views import _linkify, _url_name_for_change_view

logger = logging.getLogger(__name__)


class SCMCheckInfo(RalphDetailView):
    icon = "cogs"
    label = "SCM info"
    name = "scm_info"
    url_name = None
    template_name = "configuration_management/scminfo/scm_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            check = self.object.scmstatuscheck
        except ObjectDoesNotExist:
            check = None
        context["scm_check"] = check

        hostname = getattr(self.object, "hostname", None)

        if hostname:
            context["scm_tool_url"] = settings.SCM_TOOL_URL.format(hostname=hostname)

        return context


class SCMStatusCheckInChangeListMixin(object):
    icon_no_scan = "-"
    icon_scan = '<i class="fa {}" aria-hidden="true"></i>'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_select_related += [
            "scmstatuscheck",
        ]
        self.list_filter += [
            ("scmstatuscheck__check_result", custom_title_filter("SCM scan status")),
            ("scmstatuscheck__last_checked", custom_title_filter("Last SCM scan date")),
        ]

    def _to_span(self, css, text):
        return '<span class="{}">{}</span>'.format(css, text)

    def scm_status_check(self, obj):
        try:
            scmstatuscheck = obj.scmstatuscheck
        except ObjectDoesNotExist:
            html = self._to_span("", self.icon_no_scan)
        else:
            check_result = SCMCheckResult.from_id(scmstatuscheck.check_result)

            html = self._to_span(
                check_result.alert, self.icon_scan.format(check_result.icon_class)
            )

            url_name = _url_name_for_change_view(type(obj), "scm_info")

            if not url_name:
                logger.error("No scm info view for obj of type: %s", type(obj))
            else:
                try:
                    url = get_admin_url(obj, url_name)
                    html = _linkify(html, url)
                except NoReverseMatch:
                    logger.error("cant reverse url for: %s, %s", obj, url_name)
        return mark_safe(html)

    scm_status_check.short_description = _("SCM status")
    scm_status_check.admin_order_field = "scmstatuscheck"
