# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.assets.models.assets import NamedMixin, Manufacturer
from ralph.data_center.models.choices import Protocol


# =============================================================================
# Databases
# =============================================================================
# TODO: maybe AssetModel, DatabaseType, VIPType, VirtualServerModel could have
# common class
class DatabaseType(NamedMixin):
    class Meta:
        verbose_name = _("database type")
        verbose_name_plural = _("databases types")
        ordering = ('name',)

    def get_count(self):
        return self.databases.count()


class Database(NamedMixin, BaseObject):
    database_type = models.ForeignKey(
        DatabaseType,
        verbose_name=_("database type"),
        related_name='databases',
    )

    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')


# =============================================================================
# VIPs
# =============================================================================
class VIPType(NamedMixin):
    class Meta:
        verbose_name = _("VIP type")
        verbose_name_plural = _("VIPs types")
        ordering = ('name',)

    def get_count(self):
        return self.vips.count()


class VIP(NamedMixin, BaseObject):
    vip_type = models.ForeignKey(
        VIPType,
        verbose_name=_('VIP type'),
        related_name='vips',
    )
    address = models.ForeignKey(
        "IPAddress",
        verbose_name=_("address"),
    )
    port = models.PositiveIntegerField(
        verbose_name=_("port"),
    )
    protocol = models.PositiveIntegerField(
        verbose_name=_("protocol"),
        choices=Protocol(),
        default=Protocol.TCP.id,
    )

    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')
        unique_together = ('address', 'port', 'protocol')

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.address, self.port)


# =============================================================================
# Virtual servers
# =============================================================================
class VirtualServerModel(NamedMixin):
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("virtual server type")
        verbose_name_plural = _("virtual servers types")
        ordering = ('name',)

    def __str__(self):
        return '{} {}' % (self.manufacturer, self.name)

    def get_count(self):
        return self.virtuals.count()


class VirtualServer(BaseObject):
    hostname = models.CharField(
        verbose_name=_('hostname'),
        blank=True,
        default=None,
        max_length=255,
        null=True
    )
    sn = models.CharField(
        verbose_name=_('sn'),
        max_length=200,
        null=True,
        blank=True,
        unique=True
    )
    model = models.ForeignKey(
        VirtualServerModel,
        related_name='virtuals',
        verbose_name=_('model'),
    )

    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')


# =============================================================================
# Cloud projects
# =============================================================================
class CloudProjectType(NamedMixin):
    class Meta:
        verbose_name = _("cloud project type")
        verbose_name_plural = _("cloud projects types")
        ordering = ('name',)

    def get_count(self):
        return self.cloud_projects.count()


class CloudProject(NamedMixin, BaseObject):
    key = models.CharField(
        verbose_name=_('key'),
        max_length=200,
        null=True,
        blank=True,
        unique=True
    )
    cloud_project_type = models.ForeignKey(
        CloudProjectType,
        verbose_name=_('cloud project type'),
        related_name='cloud_projects',
    )

    class Meta:
        verbose_name = _('cloud project')
        verbose_name_plural = _('cloud projects')
