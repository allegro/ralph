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

    class Meta:
        verbose_name = _("preboot")
        verbose_name_plural = _("preboots")


class MultipleDeploymentInitialData(TimeTrackable, EditorTrackable):
    csv = db.TextField()
    is_done = db.BooleanField(default=False)

    class Meta:
        verbose_name = _("multiple deployments initial data")
        verbose_name_plural = _("multiple deployments initial data")

    def __unicode__(self):
        return "{} - {}".format(
            self.created.strftime("%Y-%m-%d %H:%M"),
            self.created_by
        )


class Deployment(TimeTrackable):
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
    hostname = db.CharField(
        _("hostname"),
        max_length=255,
        unique=True,
    )
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
    puppet_certificate_revoked = db.BooleanField(default=False)
    multiple_deployment = models.ForeignKey(
        MultipleDeploymentInitialData,
        verbose_name=_("initiated by multiple deployment"), null=True,
        blank=True, default=None, on_delete=models.SET_NULL, editable=False
    )

    class Meta:
        verbose_name = _("deployment")
        verbose_name_plural = _("deployments")

    def __unicode__(self):
        return "{} as {}/{} - {}".format(
            self.hostname,
            self.venture.path,
            self.venture_role.path,
            self.get_status_display(),
        )

    def save(self, *args, **kwargs):
        if self.status_changed():
            self.status_lastchanged = datetime.datetime.now()
        super(Deployment, self).save(*args, **kwargs)

    def status_changed(self):
        return not self.id or 'status' in self.dirty_fields


class DeploymentPoll(db.Model, WithConcurrentGetOrCreate):
    key = db.CharField(max_length=255)
    date = db.DateTimeField()
    checked = db.BooleanField(default=False)





# Import all the plugins
import ralph.deployment.plugins   # noqa
