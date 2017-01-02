# -*- coding: utf-8 -*-
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.attachments.models import AttachmentItem
from ralph.lib.custom_fields.models import WithCustomFieldsMixin
from ralph.lib.mixins.models import TaggableMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin
from ralph.lib.permissions.models import PermissionsBase
from ralph.lib.polymorphic.models import (
    Polymorphic,
    PolymorphicBase,
    PolymorphicQuerySet
)
from ralph.lib.transitions.models import TransitionWorkflowBase

BaseObjectMeta = type(
    'BaseObjectMeta', (
        PolymorphicBase,
        PermissionsBase,
        TransitionWorkflowBase
    ), {}
)


class HostFilterMixin(object):
    def dc_hosts(self):
        """
        Filter objects to get only hosts.

        Proper content types:
        * Cluster
        * DataCenterAsset
        * VirtualServer
        * CloudHost
        """
        from ralph.data_center.models import Cluster, DataCenterAsset
        from ralph.virtual.models import CloudHost, VirtualServer
        return self.filter(
            content_type__in=ContentType.objects.get_for_models(
                Cluster, DataCenterAsset, VirtualServer, CloudHost
            ).values()
        )


class BaseObjectPolymorphicQuerySet(HostFilterMixin, PolymorphicQuerySet):
    pass


class BaseObject(
    Polymorphic,
    TaggableMixin,
    PermByFieldMixin,
    TimeStampMixin,
    WithCustomFieldsMixin,
    models.Model,
    metaclass=BaseObjectMeta
):
    polymorphic_objects = BaseObjectPolymorphicQuerySet.as_manager()
    attachments = GenericRelation(AttachmentItem)

    """Base object mixin."""
    # TODO: dynamically limit parent basing on model
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children'
    )
    remarks = models.TextField(blank=True)
    service_env = models.ForeignKey('ServiceEnvironment', null=True)

    @property
    def _str_with_type(self):
        return '{}: {}'.format(
            ContentType.objects.get_for_id(self.content_type_id),
            str(self)
        )

    configuration_path = models.ForeignKey(
        'ConfigurationClass',
        null=True,
        blank=True,
        verbose_name=_('configuration path'),
        help_text=_(
            'path to configuration for this object, for example path to puppet '
            'class'
        )
    )

    @property
    def service(self):
        return self.service_env.service if self.service_env else None

    def get_absolute_url(self):
        return reverse('admin:view_on_site', args=(
            self.content_type_id,
            self.pk
        ))
