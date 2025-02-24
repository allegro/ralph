# -*- coding: utf-8 -*-
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.urls import NoReverseMatch
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.helpers import get_admin_url
from ralph.admin.mixins import RalphAdmin, RalphTabularInline
from ralph.admin.sites import ralph_site
from ralph.admin.views.extra import RalphDetailView
from ralph.security.models import SecurityScan, Vulnerability

logger = logging.getLogger(__name__)


@lru_cache()
def _url_name_for_change_view(obj_class, view_name):
    """
    Returns `url_name` attribute of view named by `view_name` or None

    Takes registred ModelAdmin for `obj_class` and searches its `change_views`
    for view with name `view_name`.  Then returns `url_name` for found view.
    """
    if obj_class not in ralph_site._registry:
        return None
    model_admin = ralph_site._registry[obj_class]
    found_view = None
    for change_view in getattr(model_admin, "change_views", []):
        if getattr(change_view, "name", "") == view_name:
            found_view = change_view
            break
    return getattr(found_view, "url_name", None)


def _linkify(to_linkify, url):
    return '<a href="{}">{}</a>'.format(url, to_linkify)


class ScanStatusMixin(object):
    field_name = _("Security scan")

    def _to_span(self, css, text):
        return '<span class="{}">{}</span>'.format(css, text)

    def scan_status(self, obj):
        try:
            scan = obj.securityscan
        except ObjectDoesNotExist:
            html = self._to_span("", "No scan")
        else:
            if scan.is_ok:
                if not scan.is_patched:
                    html = self._to_span("alert", "Vulnerable")
                else:
                    html = self._to_span("success", "Host clean")
            else:
                html = self._to_span("warning", "Scan failed")

            url_name = _url_name_for_change_view(type(obj), "security_info")
            if not url_name:
                logger.error("No security view for obj of type: %s", type(obj))
            else:
                try:
                    url = get_admin_url(obj, url_name)
                    html = _linkify(html, url)
                except NoReverseMatch:
                    logger.error("cant reverse url for: %s, %s", obj, url_name)
        return mark_safe(html)


class ScanStatusInChangeListMixin(ScanStatusMixin):
    def __init__(self, *args, **kwargs):
        self.scan_status.__func__.short_description = self.field_name

        super().__init__(*args, **kwargs)
        self.list_select_related += [
            "securityscan",
        ]


class ScanStatusInTableMixin(ScanStatusMixin):
    def __init__(self, *args, **kwargs):
        self.scan_status.__func__.title = self.field_name
        super().__init__(*args, **kwargs)


@register(Vulnerability)
class VulnerabilityAdmin(RalphAdmin):
    search_fields = [
        "name",
    ]


class VulnerabilitiesInline(RalphTabularInline):
    verbose_name = "Vulnerability"
    verbose_name_plural = "Vulnerabilities"
    model = SecurityScan.vulnerabilities.through
    raw_id_fields = ("vulnerability",)


@register(SecurityScan)
class SecurityScan(RalphAdmin):
    fields = (
        "last_scan_date",
        "scan_status",
        "next_scan_date",
        "details_url",
        "rescan_url",
    )
    list_select_related = (
        "base_object",
        "base_object__content_type",
    )

    inlines = [
        VulnerabilitiesInline,
    ]


class SecurityInfo(RalphDetailView):
    icon = "lock"
    label = "Security Info"
    name = "security_info"
    url_name = None
    template_name = "security/securityinfo/security_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            scan = self.object.securityscan
        except ObjectDoesNotExist:
            scan = None
        context["security_scan"] = scan
        return context
