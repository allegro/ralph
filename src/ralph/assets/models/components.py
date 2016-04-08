# -*- coding: utf-8 -*-
import re

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
    base_object = models.ForeignKey(BaseObject, related_name='%(class)s')
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
    label = models.CharField(verbose_name=_('name'), max_length=255)
    mac = models.CharField(
        verbose_name=_('MAC address'), unique=True,
        validators=[mac_validator], max_length=24
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
