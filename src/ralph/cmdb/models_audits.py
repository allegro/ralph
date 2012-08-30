#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from celery.task import task
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.choices import Choices
from lck.django.common.models import TimeTrackable

from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.cmdb.integration.exceptions import IssueTrackerException
from ralph.cmdb.models_common import getfunc
from ralph.cmdb.models import CI

ACTION_IN_PROGRESS=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['IN_PROGRESS']
ACTION_IN_DEPLOYMENT=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['IN_DEPLOYMENT']
ACTION_RESOLVED_FIXED=settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['RESOLVED_FIXED']
DEFAULT_ASSIGNEE=settings.ISSUETRACKERS['default']['OPA']['DEFAULT_ASSIGNEE']

class AuditStatus(Choices):
    _ = Choices.Choice

    created = _('created')
    accepted = _('accepted')
    rejected = _('rejected')
    closed = _('closed')


class Auditable(TimeTrackable):
    """ Base abstract class for keeping track of acceptation of change.
    May be attribute change, or some custom workflow change.
    Object, old value and new value is not stored here, giving ability to set it
    according to custom neeeds.

    If implementing attribute change, please do something like this:

    class AttributeChange(Auditable):
        object = ...
        new_attribute =  ..
        old_attribute = ...

    """
    user = models.ForeignKey('auth.User',
           verbose_name=_("user"), null=True,
           blank=True, default=None,
           on_delete=models.SET_NULL
    )
    status_lastchanged = models.DateTimeField(verbose_name=_("date"))
    #status = models.IntegerField(max_length=11,
    #        choices=AuditStatus(), default=AuditStatus.created.id)
    issue_key = models.CharField(verbose_name='External ticket key number',
            max_length=30, blank=True,
            null=True, default=None)

    class Meta:
        abstract = True
        verbose_name = 'Auditable base class'

    def status_changed(self):
        # newly created
        if not self.id:
            return True
        # didnt change status
        if 'status' not in self.dirty_fields:
            return False
        # changed status
        dirty_statusid = self.dirty_fields['status']
        if not dirty_statusid or dirty_statusid == self.status:
            return False
        else:
            return True

    def synchronize_status(self, new_status):
        ch = DeploymentStatus.from_id(new_status)
        transition_id = bugtracker_transition_ids.get(ch.name)
        getfunc(transition_issue)(type(self), self.id, transition_id)

    def save(self, *args, **kwargs):
        if kwargs.get('user'):
            self.user = kwargs.get('user')
        first_run = False
        if not self.id:
            first_run = True
        if self.status_changed():
            new_status = self._fields_as_dict().get('status')
            if new_status and not first_run:
                self.synchronize_status(new_status)
            self.status_lastchanged=datetime.now()
        # we need change id
        super(Auditable, self).save(*args, **kwargs)
        # now fire celery task if just created
        if first_run:
            self.fire_issue()


bugtracker_transition_ids = dict(
    opened=None,
    in_progress=ACTION_IN_PROGRESS,
    in_deployment=ACTION_IN_DEPLOYMENT,
    resolved_fixed=ACTION_RESOLVED_FIXED,
)


@task
def transition_issue(auditable_class, auditable_id, transition_id, retry_count=1):
    try:
        auditable_object = auditable_class.objects.get(id=auditable_id)
        tracker = IssueTracker()
        tracker.transition_issue(
            issue_key=auditable_object.issue_key,
            transition_id=transition_id,
        )
    except IssueTrackerException as e:
        raise transition_issue.retry(exc=e, args=[auditable_class,
            auditable_id, transition_id, retry_count + 1], countdown=60 * (2 ** retry_count),
            max_retries=15) # up to 22 days

@task
def create_issue(auditable_class, auditable_id, params, retry_count=1):
    """
    We create 2 IssueTracker requests for IssueTracker here.
    1) Check if assignee exists in IssueTracker
    2) Create issue with back-link for acceptance
    3) #TODO: assignes needs to be set per subtask
    """
    auditable_object = auditable_class.objects.get(id=auditable_id)
    try:
        tracker = IssueTracker()
        if params.get('ci_uid'):
            ci = CI.objects.get(uid=params.get('ci_uid'))
        else:
            ci = None
        if not tracker.user_exists(params.get('technical_assignee')):
            tuser = DEFAULT_ASSIGNEE
        else:
            tuser = params.get('technical_assignee')
        if not tracker.user_exists(params.get('business_assignee')):
            buser = DEFAULT_ASSIGNEE
        else:
            buser = params.get('business_assignee')
        issue = tracker.create_issue(
                issue_type=params.get('issue_type'),
                description=params.get('description'),
                summary=params.get('summary'),
                ci=ci,
                assignee=DEFAULT_ASSIGNEE,
                technical_assignee=tuser,
                business_assignee=buser,
                start=auditable_object.created.isoformat(),
                end='',
                template=params.get('template'),
        )
        auditable_object.status_lastchanged = datetime.now()
        auditable_object.issue_key = issue.get('key')
        auditable_object.save()
    except IssueTrackerException as e:
        raise create_issue.retry(exc=e, args=[auditable_class,
            auditable_id, params, retry_count + 1], countdown=60 * (2 ** retry_count),
            max_retries=15) # up to 22 days


