# -*- coding: utf-8 -*-
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ComponentType, EthernetSpeed
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin

MAC_RE = re.compile(r'^\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\s*$')
MAC_ERROR_MSG = "'%(value)s' is not a valid MAC address."
mac_validator = RegexValidator(regex=MAC_RE, message=MAC_ERROR_MSG)


class ComponentModel(AutocompleteTooltipMixin, NamedMixin, models.Model):
    speed = models.PositiveIntegerField(
        verbose_name=_('speed (MHz)'),
        default=0,
        blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name=_('number of cores'),
        default=0,
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'),
        default=0,
        blank=True,
    )
    type = models.PositiveIntegerField(
        verbose_name=_('component type'),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    family = models.CharField(blank=True, default='', max_length=128)

    autocomplete_tooltip_fields = [
        'speed',
        'cores',
        'size',
        'type',
        'family',
    ]

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family')
        verbose_name = _('component model')
        verbose_name_plural = _('component models')

    def __str__(self):
        return self.name


class Component(TimeStampMixin, models.Model):
    base_object = models.ForeignKey(BaseObject, related_name='%(class)s_set')
    model = models.ForeignKey(
        ComponentModel,
        verbose_name=_('model'),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True


class GenericComponent(Component):
    label = models.CharField(
        verbose_name=_('label'), max_length=255, blank=True,
        null=True, default=None,
    )
    sn = NullableCharField(
        verbose_name=_('vendor SN'), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )

    class Meta:
        verbose_name = _('generic component')
        verbose_name_plural = _('generic components')


class Ethernet(Component):
    label = NullableCharField(
        verbose_name=_('name'), max_length=255, blank=True, null=True
    )
    mac = NullableCharField(
        verbose_name=_('MAC address'), unique=True,
        validators=[mac_validator], max_length=24, null=True, blank=True
    )
    speed = models.PositiveIntegerField(
        verbose_name=_('speed'), choices=EthernetSpeed(),
        default=EthernetSpeed.unknown.id,
    )

    class Meta:
        verbose_name = _('ethernet')
        verbose_name_plural = _('ethernets')
        ordering = ('base_object', 'mac')

    def __str__(self):
        return '{} ({})'.format(self.label, self.mac)

    def _validate_expose_in_dhcp_and_mac(self):
        """
        Check if mac is not empty when exposing in DHCP.
        """
        from ralph.networks.models import IPAddress
        try:
            if not self.mac and self.ipaddress.dhcp_expose:
                raise ValidationError(
                    _('MAC cannot be empty if record is exposed in DHCP')
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
                        raise ValidationError(
                            'Cannot change MAC when exposing in DHCP'
                        )
            except IPAddress.DoesNotExist:
                pass

    def clean(self):
        errors = {}
        for validator in [
            super().clean,
            self._validate_expose_in_dhcp_and_mac,
            self._validate_change_when_exposing_in_dhcp
        ]:
            try:
                validator()
            except ValidationError as e:
                e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)


class Memory(Component):
    label = models.CharField(verbose_name=_('name'), max_length=255)
    size = models.PositiveIntegerField(verbose_name=_("size (MiB)"))
    speed = models.PositiveIntegerField(
        verbose_name=_("speed (MHz)"), null=True, blank=True,
    )
    slot_no = models.PositiveIntegerField(
        verbose_name=_("slot number"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _('memory')
        verbose_name_plural = _('memories')

    def __str__(self):
        if self.slot_no:
            return '#{}: {} ({} MiB)'.format(
                self.slot_no, self.label, self.size
            )
        return '{} ({} MiB)'.format(self.label, self.size)
