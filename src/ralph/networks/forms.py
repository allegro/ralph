# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.forms import ValidationError
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.components import Ethernet
from ralph.lib.field_validation.form_fields import CharFormFieldWithAutoStrip
from ralph.networks.models import IPAddress

DHCP_EXPOSE_LOCKED_FIELDS = ["hostname", "address", "mac", "dhcp_expose"]


def validate_is_management(forms):
    """
    Validate is_management field in IpAddress formset
    """
    is_management = []
    for form in forms:
        cleaned_data = form.cleaned_data
        if cleaned_data and not cleaned_data.get("DELETE", False):
            is_management.append(cleaned_data.get("is_management"))

    count_management_ip = is_management.count(True)
    if is_management and count_management_ip > 1:
        raise ValidationError(
            ("Only one management IP address can be assigned " "to this asset")
        )


class EthernetLockDeleteForm(forms.ModelForm):
    ip_fields = []

    class Meta:
        model = Ethernet
        fields = ["mac", "model_name", "label", "speed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # assign ip attached to ethernet
        try:
            self.ip = self.instance.ipaddress
        except AttributeError:
            self.ip = None
        else:
            for field in self.ip_fields:
                self.fields[field].initial = self.ip.__dict__[field]

        # make fields readonly if row (mac, ip, hostname) exposed in DHCP
        if self._dhcp_expose_should_lock_fields:
            for field_name in DHCP_EXPOSE_LOCKED_FIELDS:
                try:
                    field = self.fields[field_name]
                except KeyError:
                    pass
                else:
                    if isinstance(field, forms.BooleanField):
                        field.widget.attrs["disabled"] = True
                    field.widget.attrs["readonly"] = True

    @property
    def _dhcp_expose_should_lock_fields(self):
        """
        Return True if row should be locked for changes if it's exposed in DHCP.
        """
        return (
            settings.DHCP_ENTRY_FORBID_CHANGE
            and self.instance
            and self.instance.pk
            and self.ip
            and self.ip.dhcp_expose
        )


class SimpleNetworkForm(EthernetLockDeleteForm):
    """
    This form handles both Ethernet and IPAddress models.

    Validations and checks:
    * at least one of MAC and IP address is required
    * when address is empty, none of ip fields (is_management, hostname etc)
        could be filled

    Notes:
    * IP address could not exist before (there is no lookup by IP address - for
        new row or row with empty address before, new IPAddress is created.
        Otherwise existing IPAddress attached to Ethernet is used - when IP
        changes, validation if this address does not exist before is made).
    * This form handles exposing (hostname, mac, ip) trio in DHCP. If `expose
        in DHCP` is selected, none of these field could be changed (including
        `dhcp_expose`) or row could not be deleted. User need to perform
        transition changing `dhcp_expose` field (to False) - then row could be
        modified/deleted.
    """

    hostname = CharFormFieldWithAutoStrip(label="Hostname", required=False)
    address = forms.GenericIPAddressField(
        label="IP address", required=False, protocol="IPv4"
    )

    ip_fields = ["hostname", "address"]

    class Meta:
        model = Ethernet
        fields = [
            "hostname",
            "address",
            "mac",
        ]

    def _validate_ip_uniquness(self, address):
        """
        Validate if there is any IP with passed address (exluding current ip).
        """
        qs = IPAddress.objects.filter(address=address)
        if self.ip:
            qs = qs.exclude(pk=self.ip.pk)
        if qs.exists():
            raise ValidationError(
                _("Address %(ip)s already exist."),
                params={"ip": address},
            )

    def _validate_hostame_uniqueness_in_dc(self):
        address = self.cleaned_data["address"]
        new_hostname = self.cleaned_data["hostname"]
        if not self.ip or self.ip.address != address:
            ip = IPAddress(address=address, hostname=new_hostname)
        else:
            ip = self.ip
        ip.validate_hostname_uniqueness_in_dc(new_hostname)

    def clean_address(self):
        if self._dhcp_expose_should_lock_fields:
            # if address is locked, just return current address
            address = self.ip.address
        else:
            address = self.cleaned_data["address"]
            self._validate_ip_uniquness(address)
        return address

    def clean_mac(self):
        if self._dhcp_expose_should_lock_fields:
            # if mac is locked, just return current mac
            return self.instance.mac
        return self.cleaned_data["mac"]

    def clean_hostname(self):
        if self._dhcp_expose_should_lock_fields:
            # if mac is locked, just return current hostname
            return self.ip.hostname
        return self.cleaned_data["hostname"]

    def clean_dhcp_expose(self):
        """
        Check if hostname, address and mac are filled when entry should be
        exposed in DHCP
        """
        if self._dhcp_expose_should_lock_fields:
            # if dhcp expose is locked, just return current address
            return self.ip.dhcp_expose
        dhcp_expose = self.cleaned_data["dhcp_expose"]
        if dhcp_expose:
            if not self.cleaned_data.get("address"):
                raise ValidationError(
                    _("Cannot expose in DHCP without IP address"),
                )
            if not self.cleaned_data.get("hostname"):
                raise ValidationError(
                    _("Cannot expose in DHCP without hostname"),
                )
            if not self.cleaned_data.get("mac"):
                raise ValidationError(
                    _("Cannot expose in DHCP without MAC address"),
                )
            self._validate_hostame_uniqueness_in_dc()
        return dhcp_expose

    def _validate_mac_address(self):
        """
        Validate if any of mac and address are filled.
        """
        fields = ["mac", "address"]
        if not any([self.cleaned_data.get(field) for field in fields]):
            raise ValidationError(
                _("At least one of {} is required".format(", ".join(fields)))
            )

    def _validate_ip_fields(self):
        """
        If adddress is not filled and any other ip field is filled, raise error.
        """
        ip_fields_without_address = [f for f in self.ip_fields if f != "address"]
        if not self.cleaned_data.get("address") and any(
            [self.cleaned_data.get(f) for f in ip_fields_without_address]
        ):
            raise ValidationError(
                "Address is required when one of {} is filled".format(
                    ", ".join(ip_fields_without_address)
                )
            )

    def clean(self):
        super().clean()
        self._validate_mac_address()
        self._validate_ip_fields()

    def save(self, commit=True):
        obj = super().save(commit=True)
        ip_values = {
            key: value
            for key, value in self.cleaned_data.items()
            if key in self.ip_fields
        }
        if self.ip:
            self.ip.__dict__.update(ip_values)
            self.ip.save()
        elif ip_values["address"]:
            # save IP only if there is address passed in the form
            IPAddress.objects.create(ethernet=obj, **ip_values)
        return obj


class SimpleNetworkWithManagementIPForm(SimpleNetworkForm):
    is_management = forms.BooleanField(label="Is management", required=False)

    ip_fields = ["hostname", "address", "is_management"]


class NetworkForm(SimpleNetworkWithManagementIPForm):
    dhcp_expose = forms.BooleanField(label=_("Expose in DHCP"), required=False)

    ip_fields = ["hostname", "address", "is_management", "dhcp_expose"]

    class Meta:
        model = Ethernet
        fields = ["hostname", "address", "mac", "is_management", "label", "dhcp_expose"]


class NetworkInlineFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_delete and form._dhcp_expose_should_lock_fields:
            # many other places in Django code depends on DELETE field
            # so instead of deleting it here, we're just hiding it and validate
            # if it's not used
            form.fields[DELETION_FIELD_NAME].widget.attrs["hidden"] = True

    def clean(self):
        result = super().clean()
        validate_is_management(self.forms)
        self._validate_can_delete()
        return result

    def _validate_can_delete(self):
        """
        Forbid deletion of rows with 'dhcp_entry' enabled.
        """
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            data = form.cleaned_data
            if data.get("DELETE") and form._dhcp_expose_should_lock_fields:
                raise ValidationError("Cannot delete entry if its exposed in DHCP")
