#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import datetime

from django.db import models
from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from dj.choices import Choices
from dj.choices.fields import ChoiceField
from lck.django.common.models import (
    MACAddressField, Named, TimeTrackable,
    WithConcurrentGetOrCreate, EditorTrackable,
)

from ralph.discovery.models import Device


class DeploymentStatus(Choices):
    _ = Choices.Choice

    open = _('open')
    in_progress = _('in progress')
    done = _('done')


class FileType(Choices):
    _ = Choices.Choice

    LINUX = Choices.Group(0)
    kernel = _("kernel")
    initrd = _("initrd")

    CONFIGURATION = Choices.Group(40)
    boot_ipxe = _("boot_ipxe")
    kickstart = _("kickstart")

    OTHER = Choices.Group(100)
    other = _("other")


def preboot_file_name(instance, filename):
    return os.sep.join(('pxe', instance.get_ftype_display(), instance.name))


class PrebootFile(Named):
    ftype = ChoiceField(
        _("file type"),
        choices=FileType,
        default=FileType.other,
    )
    raw_config = db.TextField(
        _("raw config"),
        blank=True,
        help_text=_("All newline characters will be converted to Unix \\n "
                    "newlines. You can use {{variables}} in the body. "
                    "Available variables: filename, filetype, mac, ip, "
                    "hostname, venture and venture_role."),
    )
    file = db.FileField(
        _("file"),
        upload_to=preboot_file_name,
        null=True,
        blank=True,
        default=None,
    )
    description = db.TextField(
        verbose_name=_("description"),
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("preboot file")
        verbose_name_plural = _("preboot files")

    def __unicode__(self):
        return "_{}: {}".format(self.get_ftype_display(), self.name)

    def get_filesize_display(self):
        template = """binary {size:.2f} MB"""
        return template.format(
            size=self.file.size / 1024 / 1024,
        )


class Preboot(Named, TimeTrackable):
    files = db.ManyToManyField(
        PrebootFile,
        null=True,
        blank=True,
        verbose_name=_("files"),
    )
    description = db.TextField(
        verbose_name=_("description"),
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("preboot")
        verbose_name_plural = _("preboots")
        ordering = ('name',)


class MassDeployment(TimeTrackable, EditorTrackable):
    csv = db.TextField(blank=True)
    generated_csv = db.TextField(blank=True)
    is_done = db.BooleanField(default=False)

    class Meta:
        verbose_name = _("mass deployment")
        verbose_name_plural = _("mass deployments")
        ordering = ('-created',)

    def __unicode__(self):
        return "{} - {}".format(
            self.created.strftime("%Y-%m-%d %H:%M"),
            self.created_by
        )


class AbstractDeployment(db.Model):
    user = models.ForeignKey(
        'auth.User', verbose_name=_("user"), null=True,
        blank=True, default=None, on_delete=models.SET_NULL
    )
    status_lastchanged = models.DateTimeField(
        default=datetime.datetime.now,
        verbose_name=_("last status change"),
        help_text=_("the date of the last status change"),
    )
    device = db.ForeignKey(Device)
    mac = MACAddressField()
    status = db.IntegerField(
        choices=DeploymentStatus(),
        default=DeploymentStatus.open.id,
    )
    ip = db.IPAddressField(_("IP address"))
    preboot = db.ForeignKey(
        Preboot,
        verbose_name=_("preboot"),
        null=True,
        on_delete=db.SET_NULL,
    )
    venture = db.ForeignKey(
        'business.Venture',
        verbose_name=_("venture"),
        null=True,
        on_delete=db.SET_NULL,
    )
    venture_role = db.ForeignKey(
        'business.VentureRole',
        null=True,
        verbose_name=_("role"),
        on_delete=db.SET_NULL,
    )
    done_plugins = db.TextField(
        _("done plugins"),
        blank=True,
        default='',)
    is_running = db.BooleanField(
        _("is running"),
        default=False,
    )   # a database-level lock for deployment-related tasks
    mass_deployment = db.ForeignKey(
        MassDeployment,
        verbose_name=_("initiated by mass deployment"), null=True,
        blank=True, default=None, on_delete=models.SET_NULL, editable=False
    )

    class Meta:
        abstract = True

    def __unicode__(self):
        return "{} as {}/{} - {}".format(
            self.hostname,
            self.venture.path if self.venture else '-',
            self.venture_role.path if self.venture_role else '-',
            self.get_status_display(),
        )


class ArchivedDeployment(AbstractDeployment, TimeTrackable):
    hostname = db.CharField(
        _("hostname"),
        max_length=255,
        unique=False,
    )

    class Meta:
        verbose_name = _("archived deployment")
        verbose_name_plural = _("archived deployments")
        ordering = ('-created',)

    def __unicode__(self):
        return "{} as {}/{} - {} (archived)".format(
            self.hostname,
            self.venture.path if self.venture else '-',
            self.venture_role.path if self.venture_role else '-',
            self.get_status_display(),
        )


class Deployment(AbstractDeployment, TimeTrackable):
    hostname = db.CharField(
        _("hostname"),
        max_length=255,
        unique=True,
    )

    class Meta:
        verbose_name = _("deployment")
        verbose_name_plural = _("deployments")
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        if self.status_changed():
            self.status_lastchanged = datetime.datetime.now()
        super(Deployment, self).save(*args, **kwargs)

    def status_changed(self):
        return not self.id or 'status' in self.dirty_fields

    def archive(self):
        data = {}
        for field in self._meta.fields:
            if field.name == 'id':
                continue
            data[field.name] = getattr(self, field.name)
        ArchivedDeployment.objects.create(**data)
        self.delete()

    def __unicode__(self):
        return "{} as {}/{} - {}".format(
            self.hostname,
            self.venture.path if self.venture else '-',
            self.venture_role.path if self.venture_role else '-',
            self.get_status_display(),
        )


class DeploymentPoll(db.Model, WithConcurrentGetOrCreate):
    key = db.CharField(max_length=255)
    date = db.DateTimeField()
    checked = db.BooleanField(default=False)


# Import all the plugins
import ralph.deployment.plugins   # noqa
