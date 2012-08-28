#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from lck.django.common.models import TimeTrackable
from lck.django.choices import Choices
from ralph.discovery.models import Device
from ralph.cmdb.integration.bugtracker import Bugtracker
from ralph.cmdb.models import CI
from ralph.cmdb.util import  getfunc
from django.conf import settings

from celery.task import task

class AuditStatus(Choices):
    _ = Choices.Choice

    created = _('created')
    waiting = _('waiting')
    accepted = _('accepted')
    rejected = _('rejected')
    closed = _('closed')


class Auditable(TimeTrackable):
    user = models.ForeignKey('auth.User',
           verbose_name=_("user"), null=True,
           blank=True, default=None,
           on_delete=models.SET_NULL
    )
    status_lastchanged = models.DateTimeField(verbose_name=_("date"),
            default=datetime.now)
    status = models.IntegerField(max_length=11,
            choices=AuditStatus())
    external_key = models.CharField(verbose_name='External ticket key number',
            max_length=30, blank=True,
            null=True, default=None)

    class Meta:
        abstract = True
        verbose_name = 'Auditable base class'


class Deployment(Auditable):
    device = models.ForeignKey(Device)

    def status_changed(self):
        if not self.id or 'status_id' not in self.dirty_fields:
            return False
        dirty_statusid = self.dirty_fields['status_id']
        if not dirty_statusid or dirty_statusid == self.status_id:
            return False
        else:
            return True

    def save(self, *args, **kwargs):
        if self.status_changed():
            self.status_id = datetime.datetime.now()
        if not self.id:
            getfunc(create_issue)(Deployment, self.id)
        return super(Deployment, self).save(*args, **kwargs)


@task
def create_issue(auditable_class, auditable_id,
        params,  retry_count=1):
    default_assignee = settings.JIRA_OPA_DEFAULT_ASSIGNEE
    jira_opa_template = settings.JIRA_OPA_TEMPLATE
    try:
        tracker = Bugtracker()
        if params.get('ci_uid'):
            ci = CI.objects.get(uid=params.get('ci_uid'))
        else:
            ci = None
        if not tracker.user_exists(params.get('user')):
            user = default_assignee
        else:
            user = ''
        auditable_object = auditable_class.objecs.get(id=auditable_id)
        issue = tracker.create_audit_issue(
                description=params.get('description'),
                summary=params.get('summary'),
                ci=ci,
                assignee=user,
                start=auditable_object.created.isoformat(),
                end='',
                template=jira_opa_template,
        )
        auditable_object.status = AuditStatus.waiting.id
    except Exception as e:
        raise create_issue.retry(exc=e, args=[auditable_class,
            auditable_id, params, retry_count + 1], countdown=60 * (2 ** retry_count),
            max_retries=15) # 22 days



