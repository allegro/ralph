#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import unicodedata

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db import models as db
from django.dispatch.dispatcher import Signal
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from dj.choices import Choices
from dj.choices.fields import ChoiceField
from lck.django.common.models import MACAddressField, Named, TimeTrackable,\
                                    WithConcurrentGetOrCreate

from ralph.cmdb.models import CI
from ralph.cmdb.models_audits import Auditable
from ralph.discovery.models import Device


# This signal is fired, when deployment is accepted in Bugtracker.
# note, that you should manually change deployment statuses.
deployment_accepted = Signal(providing_args=['deployment_id'])


# Sanity checks - when Issue Tracker engine set to '', or some fields
# are missing - fallback to NullIssueTracker engine
NULL_ISSUE_TRACKER=False
try:
    # engine is set?
    if settings.ISSUETRACKERS['default']['ENGINE']:
        ACTION_IN_PROGRESS=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['IN_PROGRESS']
        ACTION_IN_DEPLOYMENT=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['IN_DEPLOYMENT']
        ACTION_RESOLVED_FIXED=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['RESOLVED_FIXED']
        DEFAULT_ASSIGNEE=settings.ISSUETRACKERS['default']['OPA']['DEFAULT_ASSIGNEE']
        NULL_ISSUE_TRACKER=False
    else:
        NULL_ISSUE_TRACKER=True
except KeyError as e:
    # some keys not set
    raise ImproperlyConfigured("Expected %r in ISSUETRACKERS configuration." % e)
    NULL_ISSUE_TRACKER=True

if NULL_ISSUE_TRACKER:
    ACTION_IN_PROGRESS=''
    ACTION_IN_DEPLOYMENT=''
    ACTION_RESOLVED_FIXED=''
    DEFAULT_ASSIGNEE=''


bugtracker_transition_ids = dict(
    opened=None,
    in_progress=ACTION_IN_PROGRESS,
    in_deployment=ACTION_IN_DEPLOYMENT,
    resolved_fixed=ACTION_RESOLVED_FIXED,
)

def normalize_owner(owner):
    # Polish Ł is not handled properly
    owner = owner.name.lower().replace(' ', '.').replace('Ł', 'L').replace('ł', 'l')
    return unicodedata.normalize('NFD', owner).encode('ascii', 'ignore')


def get_technical_owner(device):
    if not device.venture:
        return ''
    owners = device.venture.technical_owners()
    return normalize_owner(owners[0]) if owners else None


def get_business_owner(device):
    if not device.venture:
        return ''
    owners = device.venture.business_owners()
    return normalize_owner(owners[0]) if owners else None


class DeploymentStatus(Choices):
    _ = Choices.Choice

    open = _('open')
    in_progress = _('in progress')
    in_deployment = _('in deployment')
    resolved_fixed = _('resolved fixed')


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
    ftype = ChoiceField(verbose_name=_("file type"), choices=FileType,
        default=FileType.other)
    raw_config = db.TextField(verbose_name=_("raw config"), blank=True)
    file = db.FileField(verbose_name=_("file"), upload_to=preboot_file_name,
        null=True, blank=True, default=None)

    class Meta:
        verbose_name = _("preboot file")
        verbose_name_plural = _("preboot files")

    def __unicode__(self):
        return "_{}: {}".format(self.get_ftype_display(), self.name)

    def get_filesize_display(self):
        template = """binary {size:.2f} MB"""
        return template.format(
            size=self.file.size/1024/1024,
        )


class Preboot(Named, TimeTrackable):
    files = db.ManyToManyField(PrebootFile, null=True, blank=True,
        verbose_name=_("files"))

    class Meta:
        verbose_name = _("preboot")
        verbose_name_plural = _("preboots")


class Deployment(Auditable):
    device = db.ForeignKey(Device)
    mac =  MACAddressField()
    status = db.IntegerField(choices=DeploymentStatus(),
        default=DeploymentStatus.open.id)
    ip = db.IPAddressField(verbose_name=_("IP address"))
    hostname = db.CharField(verbose_name=_("hostname"), max_length=255,
        unique=True)
    preboot = db.ForeignKey(Preboot, verbose_name=_("preboot"), null=True,
        on_delete=db.SET_NULL)
    venture = db.ForeignKey('business.Venture', verbose_name=_("venture"),
        null=True, on_delete=db.SET_NULL)
    venture_role = db.ForeignKey('business.VentureRole', null=True,
        verbose_name=_("role"), on_delete=db.SET_NULL)
    done_plugins = db.TextField(verbose_name=_("done plugins"),
        blank=True, default='')
    is_running = db.BooleanField(verbose_name=_("is running"),
        default=False) # a database-level lock for deployment-related tasks
    puppet_certificate_revoked = db.BooleanField(default=False)

    class Meta:
        verbose_name = _("deployment")
        verbose_name_plural = _("deployments")

    def create_issue(self):
        bowner = get_business_owner(self.device)
        towner = get_technical_owner(self.device)
        params = dict(
            ci_uid = CI.get_uid_by_content_object(self.device),
            description = 'Please accept in order to continue deployment.',
            summary = '%s - acceptance request for deployment' % unicode(self.device),
            technical_assignee=towner,
            business_assignee=bowner,
        )
        super(Deployment, self).create_issue(params, DEFAULT_ASSIGNEE)

    def synchronize_status(self, new_status):
        ch = DeploymentStatus.from_id(new_status)
        transition_id = bugtracker_transition_ids.get(ch.name)
        self.transition_issue(transition_id)


class DeploymentPoll(db.Model, WithConcurrentGetOrCreate):
    key = db.CharField(max_length=255)
    date = db.DateTimeField()
    checked = db.BooleanField(default=False)


@receiver(deployment_accepted, dispatch_uid='ralph.cmdb.deployment_accepted')
def handle_deployment_accepted(sender, deployment_id, **kwargs):
    # sample deployment accepted signal code.
    pass

# Import all the plugins
import ralph.deployment.plugins
