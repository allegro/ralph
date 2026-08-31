import ipaddress
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ralph.admin.mixins import RalphAdminForm
from ralph.assets.models import ObjectModelType
from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib.field_validation.form_fields import CharFormFieldWithAutoStrip
from ralph.lib.mixins.forms import AssetFormMixin, PriceFormMixin
from ralph.networks.models import IPAddress


HOSTNAME_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)


def _get_http_url(value):
    value = str(value or "")
    if not value or value != value.strip():
        return None

    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        hostname = value[:-1] if value.endswith(".") else value
        if (
            not hostname
            or len(hostname) > 253
            or any(not HOSTNAME_LABEL_RE.fullmatch(label) for label in hostname.split("."))
        ):
            return None
        host = value
    else:
        host = "[{}]".format(address.compressed) if address.version == 6 else address.compressed

    return "http://{}".format(host)


class HostLinkInput(forms.TextInput):
    def _render_with_link(self, field_html, value):
        url = _get_http_url(value)
        if not url:
            return field_html
        return format_html(
            '<div class="row collapse host-link-field">'
            '<div class="small-11 columns">{}</div>'
            '<div class="small-1 columns"><a class="postfix host-link" href="{}" '
            'target="_blank" rel="noopener noreferrer" title="Open address" '
            'aria-label="Open address"><i class="fa fa-external-link" '
            'aria-hidden="true"></i></a></div></div>',
            field_html,
            url,
        )

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        return self._render_with_link(input_html, value)

    def render_readonly(self, value):
        value_html = format_html(
            '<span class="read-only">{}</span>',
            value or "-",
        )
        return self._render_with_link(value_html, value)


class DataCenterAssetForm(PriceFormMixin, AssetFormMixin, RalphAdminForm):
    MODEL_TYPE = ObjectModelType.data_center
    management_ip = forms.GenericIPAddressField(required=False, protocol="IPv4")
    management_hostname = CharFormFieldWithAutoStrip(required=False)

    ip_fields = ["management_ip", "management_hostname"]
    host_link_fields = ["hostname"] + ip_fields
    readonly_widgets = {
        "hostname": HostLinkInput(),
        "management_ip": HostLinkInput(),
        "management_hostname": HostLinkInput(),
    }

    class Meta:
        model = DataCenterAsset
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.host_link_fields:
            field = self.fields.get(field_name)
            if field:
                field.widget = HostLinkInput(attrs=field.widget.attrs)
        for field_name in self.ip_fields:
            field = self.fields.get(field_name)
            if field:
                field.initial = getattr(self.instance, field_name)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        # save object to enable creating ethernet (and link it to
        # DataCenterAsset)
        obj.save()

        management_hostname = self.cleaned_data.get("management_hostname", obj.management_hostname)
        management_ip = self.cleaned_data.get("management_ip", obj.management_ip)
        if not management_hostname and not management_ip:
            del obj.management_ip
        else:
            obj.management_ip = management_ip
            obj.management_hostname = management_hostname
        return obj

    def _validate_mgmt_ip_is_unique(self):
        if not self.cleaned_data.get("management_ip"):
            return
        try:
            ip = IPAddress.objects.get(
                address=self.cleaned_data["management_ip"],
            )
        except IPAddress.DoesNotExist:
            pass
        else:
            if ip.base_object and ip.base_object.pk != self.instance.pk:
                ip_obj = ip.base_object.last_descendant
                msg = _(
                    'Management IP is already assigned to <a target="_blank" href="{}">{}</a>'
                ).format(ip_obj.get_absolute_url(), ip_obj)
                exc = ValidationError({"management_ip": mark_safe(msg)})
                self._update_errors(exc)

    def _validate_mgmt_hostname_is_unique(self):
        # hostname is not unique so this query could return 0, 1 or more
        # records
        if not self.cleaned_data.get("management_hostname"):
            return
        hostname_msg = None
        ips = IPAddress.objects.filter(
            hostname=self.cleaned_data["management_hostname"],
        )
        if len(ips) > 1:
            hostname_msg = _("Management hostname is already used")
        elif len(ips) == 1:
            ip = ips[0]
            if ip.base_object and ip.base_object.pk != self.instance.pk:
                hostname_obj = ip.base_object.last_descendant
                hostname_msg = _(
                    "Management hostname is already assigned to "
                    '<a target="_blank" href="{}">{}</a>'
                ).format(hostname_obj.get_absolute_url(), hostname_obj)
        if hostname_msg:
            exc = ValidationError({"management_hostname": mark_safe(hostname_msg)})
            self._update_errors(exc)

    def _clean_mgmt_ip_mgmt_hostname(self):
        if self.cleaned_data.get("management_hostname") and not self.cleaned_data.get(
            "management_ip"
        ):
            self._update_errors(
                ValidationError(
                    {
                        "management_ip": _(
                            "Management IP could not be empty when management hostname is passed"
                        )
                    }
                )
            )

    def clean(self):
        super().clean()
        self._clean_mgmt_ip_mgmt_hostname()

    def validate_unique(self):
        super().validate_unique()
        self._validate_mgmt_ip_is_unique()
        self._validate_mgmt_hostname_is_unique()
