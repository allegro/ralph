# -*- coding: utf-8 -*-
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import (
    ComponentType,
    EthernetSpeed,
    FibreChannelCardSpeed
)
from ralph.lib.mixins.fields import MACAddressField, NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)

MAC_RE = re.compile(r"^\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\s*$")
MAC_ERROR_MSG = "'%(value)s' is not a valid MAC address."
mac_validator = RegexValidator(regex=MAC_RE, message=MAC_ERROR_MSG)


# TODO(xor-xor): As discussed with @mkurek, this class should be removed,
# but since it is used in some cloud-related functionality, it will be
# removed later.
class ComponentModel(
    AdminAbsoluteUrlMixin, AutocompleteTooltipMixin, NamedMixin, models.Model
):
    speed = models.PositiveIntegerField(
        verbose_name=_("speed (MHz)"),
        default=0,
        blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name=_("number of cores"),
        default=0,
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name=_("size (MiB)"),
        default=0,
        blank=True,
    )
    type = models.PositiveIntegerField(
        verbose_name=_("component type"),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    family = models.CharField(blank=True, default="", max_length=128)

    autocomplete_tooltip_fields = [
        "speed",
        "cores",
        "size",
        "type",
        "family",
    ]

    class Meta:
        unique_together = ("speed", "cores", "size", "type", "family")
        verbose_name = _("component model")
        verbose_name_plural = _("component models")

    def __str__(self):
        return self.name


class Component(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    base_object = models.ForeignKey(
        BaseObject, related_name="%(class)s_set", on_delete=models.CASCADE
    )
    # TODO(xor-xor): This field should be removed along with ComponentModel
    # class.
    model = models.ForeignKey(
        ComponentModel,
        verbose_name=_("model"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    model_name = models.CharField(
        verbose_name=_("model name"),
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True


class GenericComponent(Component):
    label = models.CharField(
        verbose_name=_("label"),
        max_length=255,
        blank=True,
        null=True,
        default=None,
    )
    sn = NullableCharField(
        verbose_name=_("vendor SN"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = _("generic component")
        verbose_name_plural = _("generic components")


class Ethernet(Component):
    label = NullableCharField(
        verbose_name=_("label"), max_length=255, blank=True, null=True
    )
    mac = MACAddressField(
        verbose_name=_("MAC address"),
        unique=True,
        validators=[mac_validator],
        max_length=24,
        null=True,
        blank=True,
    )
    speed = models.PositiveIntegerField(
        verbose_name=_("speed"),
        choices=EthernetSpeed(),
        default=EthernetSpeed.unknown.id,
    )
    firmware_version = models.CharField(
        verbose_name=_("firmware version"),
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("ethernet")
        verbose_name_plural = _("ethernets")
        ordering = ("base_object", "mac")

    def __str__(self):
        return "{} ({})".format(self.label, self.mac)

    def _validate_expose_in_dhcp_and_mac(self):
        """
        Check if mac is not empty when exposing in DHCP.
        """
        from ralph.networks.models import IPAddress

        try:
            if not self.mac and self.ipaddress.dhcp_expose:
                raise ValidationError(
                    _("MAC cannot be empty if record is exposed in DHCP")
                )
        except IPAddress.DoesNotExist:
            pass

    def _validate_change_when_exposing_in_dhcp(self):
        """
        Check if mas has changed when entry is exposed in DHCP.
        """
        if self.pk and settings.DHCP_ENTRY_FORBID_CHANGE:
            from ralph.networks.models import IPAddress

            old_obj = self.__class__._default_manager.get(pk=self.pk)
            try:
                if old_obj.ipaddress.dhcp_expose:
                    if old_obj.mac != self.mac:
                        raise ValidationError("Cannot change MAC when exposing in DHCP")
            except IPAddress.DoesNotExist:
                pass

    def clean(self):
        errors = {}
        for validator in [
            super().clean,
            self._validate_expose_in_dhcp_and_mac,
            self._validate_change_when_exposing_in_dhcp,
        ]:
            try:
                validator()
            except ValidationError as e:
                e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)


class Memory(Component):
    size = models.PositiveIntegerField(verbose_name=_("size (MiB)"))
    speed = models.PositiveIntegerField(
        verbose_name=_("speed (MHz)"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("memory")
        verbose_name_plural = _("memory")

    def __str__(self):
        return "{} MiB ({} MHz)".format(self.size, self.speed)


class FibreChannelCard(Component):
    firmware_version = models.CharField(
        verbose_name=_("firmware version"),
        max_length=255,
        blank=True,
        null=True,
    )
    speed = models.PositiveIntegerField(
        verbose_name=_("speed"),
        choices=FibreChannelCardSpeed(),
        default=FibreChannelCardSpeed.unknown.id,
    )

    # If you need PWWN (or any other *WWN), add a separate field for
    # it instead of using/re-using this one.
    wwn = NullableCharField(
        verbose_name=_("WWN"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = _("fibre channel card")
        verbose_name_plural = _("fibre channel cards")

    def __str__(self):
        return 'model: "{}", WWN: "{}"'.format(self.model_name, self.wwn)


class Processor(Component):
    speed = models.PositiveIntegerField(
        verbose_name=_("speed (MHz)"),
        null=True,
        blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name="physical cores", null=True, blank=True
    )
    logical_cores = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("processor")
        verbose_name_plural = _("processors")

    def __str__(self):
        return "{}: {} cores ({} MHz)".format(self.model_name, self.cores, self.speed)


class Disk(Component):
    size = models.PositiveIntegerField(verbose_name=_("size (GiB)"))
    serial_number = models.CharField(
        verbose_name=_("serial number"),
        max_length=255,
        blank=True,
        null=True,
    )
    slot = models.PositiveIntegerField(
        verbose_name=_("slot number"),
        null=True,
        blank=True,
    )
    firmware_version = models.CharField(
        verbose_name=_("firmware version"),
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("disk")
        verbose_name_plural = _("disks")

    def __str__(self):
        return 'model: "{}", size: "{}"'.format(self.model_name, self.size)
