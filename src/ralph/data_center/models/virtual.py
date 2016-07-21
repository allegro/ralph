# -*- coding: utf-8 -*-
from dj.choices import Choices
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.data_center.models.mixins import WithManagementIPMixin
from ralph.lib.mixins.fields import BaseObjectForeignKey, NullableCharField
from ralph.lib.mixins.models import NamedMixin
from ralph.lib.transitions.fields import TransitionField


class Database(BaseObject):
    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')

    def __str__(self):
        return 'Database: {}'.format(self.service_env)


class VIP(BaseObject):
    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')

    def __str__(self):
        return 'VIP: {}'.format(self.service_env)


class ClusterType(NamedMixin, models.Model):
    show_master_summary = models.BooleanField(
        default=False,
        help_text=_(
            'show master information on cluster page, ex. hostname, model, '
            'location etc.'
        )
    )


class ClusterStatus(Choices):
    _ = Choices.Choice

    in_use = _('in use')
    for_deploy = _('for deploy')


class Cluster(WithManagementIPMixin, BaseObject, models.Model):
    name = models.CharField(_('name'), max_length=255, blank=True, null=True)
    hostname = NullableCharField(
        unique=True,
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('hostname')
    )
    type = models.ForeignKey(ClusterType)
    base_objects = models.ManyToManyField(
        BaseObject,
        verbose_name=_('Assigned base objects'),
        through='BaseObjectCluster',
        related_name='+',
    )
    status = TransitionField(
        default=ClusterStatus.in_use.id,
        choices=ClusterStatus(),
    )

    def __str__(self):
        return '{} ({})'.format(self.name or self.hostname, self.type)

    @cached_property
    def masters(self):
        result = []
        for obj in self.baseobjectcluster_set.all():
            if obj.is_master:
                result.append(obj)
        return result

    def _validate_name_hostname(self):
        if not self.name and not self.hostname:
            error_message = [_('At least one of name or hostname is required')]
            raise ValidationError(
                {'name': error_message, 'hostname': error_message}
            )

    def clean(self):
        errors = {}
        for validator in [
            super().clean,
            self._validate_name_hostname,
        ]:
            try:
                validator()
            except ValidationError as e:
                e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)


class BaseObjectCluster(models.Model):
    cluster = models.ForeignKey(Cluster)
    base_object = BaseObjectForeignKey(
        BaseObject,
        related_name='clusters',
        limit_models=[
            'data_center.Database',
            'data_center.DataCenterAsset',
            'virtual.CloudHost',
            'virtual.VirtualServer'
        ]
    )
    is_master = models.BooleanField(default=False)

    class Meta:
        unique_together = ('cluster', 'base_object')