# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ComponentType
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin


class ComponentModel(NamedMixin, models.Model):
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

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family')
        verbose_name = _('component model')
        verbose_name_plural = _('component models')

    def __str__(self):
        return self.name


class Component(models.Model):
    asset = models.ForeignKey(BaseObject, related_name='%(class)s')
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
