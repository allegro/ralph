#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from lck.django.common.models import TimeTrackable
from lck.django.choices import Choices


class CI_CHANGE_TYPES(Choices):
    _ = Choices.Choice

    CONF_GIT = _('Git Configuration')
    CONF_AGENT = _('Services reconfiguration')
    DEVICE = _('Device attribute change')
    ZABBIX_TRIGGER = _('Zabbix trigger')
    STATUSOFFICE = _('Status office service change')
    CI = _('CI attribute change')


class CI_CHANGE_PRIORITY_TYPES(Choices):
    _ = Choices.Choice

    NOTICE = _('Notice')
    WARNING = _('Warning')
    ERROR = _('Error')
    CRITICAL = _('Critical')


class CI_CHANGE_REGISTRATION_TYPES(Choices):
    _ = Choices.Choice

    INCIDENT = _('Incident')
    CHANGE = _('Change')
    SR = _('Service Request')
    NOT_REGISTERED = _('Not registered')


class CIChangeZabbixTrigger(TimeTrackable):
    ci = models.ForeignKey('CI', null=True)
    trigger_id = models.IntegerField(max_length=11)
    host = models.CharField(max_length=255)
    host_id = models.IntegerField(max_length=11)
    status = models.IntegerField(max_length=11)
    priority = models.IntegerField(max_length=11)
    description = models.CharField(max_length=1024)
    lastchange = models.CharField(max_length=1024)
    comments = models.CharField(max_length=1024)


class CIChangeStatusOfficeIncident(TimeTrackable):
    ci = models.ForeignKey('CI', null=True)
    time = models.DateTimeField(verbose_name=_("timestamp"), default=datetime.now)
    status = models.IntegerField(max_length=11)
    subject = models.CharField(max_length=1024)
    incident_id= models.IntegerField(max_length=11)


class CIChangeCMDBHistory(TimeTrackable):
    ci = models.ForeignKey('CI')
    time = models.DateTimeField(verbose_name=_("timestamp"), default=datetime.now)
    user = models.ForeignKey('auth.User', verbose_name=_("user"), null=True,
                           blank=True, default=None, on_delete=models.SET_NULL)
    field_name = models.CharField(max_length=64, default='')
    old_value = models.CharField(max_length=255, default='')
    new_value = models.CharField(max_length=255, default='')
    comment = models.CharField(max_length=255)

    class Meta:
        verbose_name = _("CI history change")
        verbose_name_plural = _("CI history changes")


class CIChange(TimeTrackable):
    ci = models.ForeignKey('CI', null=True, blank=True)
    type = models.IntegerField(max_length=11, choices=CI_CHANGE_TYPES(),
            null=False)
    priority = models.IntegerField(max_length=11,
            choices=CI_CHANGE_PRIORITY_TYPES(),
            null=False)
    content_type = models.ForeignKey(ContentType, verbose_name=_("content type"),
            null=True)
    object_id = models.PositiveIntegerField(
            verbose_name=_("object id"),
            null=True,
            blank=True,
    )
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    time = models.DateTimeField(verbose_name=_("timestamp"), default=datetime.now)
    message = models.CharField(max_length=1024)
    external_key = models.CharField(max_length=60, blank=True)
    registration_type = models.IntegerField(
            max_length=11,
            choices=CI_CHANGE_REGISTRATION_TYPES(),
            default=CI_CHANGE_REGISTRATION_TYPES.NOT_REGISTERED.id,
    )

    @classmethod
    def get_by_content_object(cls, content_object):
        ct = ContentType.objects.get_for_model(content_object)
        return CIChange.objects.get(object_id=content_object.id,
                content_type=ct)

    class Meta:
        unique_together = ('content_type', 'object_id')


class CIChangeGit(TimeTrackable):
    ci = models.ForeignKey('CI', null=True)
    file_paths = models.CharField(max_length=3000)
    comment = models.CharField(max_length=1000)
    author = models.CharField(max_length=200)
    changeset = models.CharField(max_length=80, unique=True, db_index=True)


class CIChangePuppet(TimeTrackable):
    ci = models.ForeignKey('CI', null=True)
    configuration_version = models.CharField(max_length=30, db_index=True)
    host = models.CharField(max_length=100)
    kind = models.CharField(max_length=30)
    time = models.DateTimeField(verbose_name=_("timestamp"), default=datetime.now)
    status = models.CharField(max_length=30)


class PuppetLog(TimeTrackable):
    cichange = models.ForeignKey('CIChangePuppet')
    source = models.CharField(max_length=100)
    message =models.CharField(max_length=1024)
    tags = models.CharField(max_length=100)
    time = models.DateTimeField()
    level = models.CharField(max_length=100)


class PuppetResourceStatus(TimeTrackable):
    cichange= models.ForeignKey('CIChangePuppet')
    change_count = models.IntegerField()
    changed = models.BooleanField()
    failed = models.BooleanField()
    skipped = models.BooleanField()
    file = models.CharField(max_length=1024)
    line = models.IntegerField()
    resource = models.CharField(max_length=300)
    resource_type = models.CharField(max_length=300)
    time = models.DateTimeField()
    title = models.CharField(max_length=100)


class CIEvent(TimeTrackable):
    ''' Abstract for CIProblem/CIIncident '''
    ci = models.ForeignKey('CI',
            null = True,
            blank = True,
    )
    time = models.DateTimeField()
    summary = models.CharField(max_length=1024)
    description = models.CharField(max_length=1024)
    jira_id = models.CharField(max_length=100)
    status = models.CharField(max_length=300)
    assignee = models.CharField(max_length=300)

    class Meta:
        abstract = True


class CIProblem(CIEvent):
    pass


class CIIncident(CIEvent):
    pass


# changes being handled by ticket registration are listed below.
REGISTER_CHANGE_TYPES=(
        CI_CHANGE_TYPES.CONF_GIT.id,
        CI_CHANGE_TYPES.DEVICE.id,
        CI_CHANGE_TYPES.CI.id,
)
