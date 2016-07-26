# -*- coding: utf-8 -*-
from dj.choices import Choices
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.assets.utils import DNSaaSPublisherMixin
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


class Cluster(DNSaaSPublisherMixin, BaseObject, models.Model):
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

#    @property
#    def publish_data(self):
#        data = (
#            #TODO:: really VENTURE or module here?
#            ('VENTURE', self.configuration_path.class_name if self.configuration_path else ''),
#            #TODO:: really ROLE or class_name here?
#            ('ROLE', self.configuration_path.module.name if self.configuration_path else ''),
#            ('MODEL', master.model.name if master else ''),
#            ('LOCATION', ' / '.join(master.get_location() if self.masters else [])),
#        )
#        publish_data = dnsaas_txt_record_data(
#            self.hostname,
#            #TODO:: user from threadlocal?
#            'john.doe',
#            settings.DNSAAS_OWNER,
#            data,
#        )
#        return publish_data
#        location, ipaddresses = [], []
#        master = None
#        if self.masters:
#            master = self.masters[0]
#            location = master.get_location()
#            ipaddresses = list(master.ipaddresses.all().values_list(
#                'address', flat=True
#            ))
#
#        return {
#            'hostname': self.hostname,
#            'model': master.model.name if master else '',
#            'configuration_path': (
#                self.configuration_path.path if self.configuration_path else ''
#            ),
#            'location': ' / '.join(location),
#            'service_env': str(self.service_env),
#            'ipaddresses': ipaddresses
#        }

    def get_location(self):
        return self.masters[0].get_location() if self.masters else None
    @property
    def model(self):
        return self.parent.model if self.parent else None


    @cached_property
    def masters(self):
        return BaseObject.polymorphic_objects.filter(
            pk__in=self.baseobjectcluster_set.filter(
                is_master=True
            ).values_list('base_object_id', flat=True)
        )

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
