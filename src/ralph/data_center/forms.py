from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphAdminForm
from ralph.assets.models import ObjectModelType
from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib.field_validation.form_fields import CharFormFieldWithAutoStrip
from ralph.lib.mixins.forms import AssetFormMixin, PriceFormMixin
from ralph.networks.models import IPAddress


class DataCenterAssetForm(PriceFormMixin, AssetFormMixin, RalphAdminForm):
    MODEL_TYPE = ObjectModelType.data_center
    management_ip = forms.GenericIPAddressField(required=False, protocol="IPv4")
    management_hostname = CharFormFieldWithAutoStrip(required=False)

    ip_fields = ["management_ip", "management_hostname"]

    class Meta:
        model = DataCenterAsset
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.ip_fields:
            field = self.fields[field_name]
            field.initial = getattr(self.instance, field_name)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        # save object to enable creating ethernet (and link it to
        # DataCenterAsset)
        obj.save()

        if (
            not self.cleaned_data["management_hostname"]
            and not self.cleaned_data["management_ip"]
        ):
            del obj.management_ip
        else:
            obj.management_ip = self.cleaned_data["management_ip"]
            obj.management_hostname = self.cleaned_data["management_hostname"]
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
                    "Management IP is already assigned to "
                    '<a target="_blank" href="{}">{}</a>'
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
                            "Management IP could not be empty when management hostname is "
                            "passed"
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
