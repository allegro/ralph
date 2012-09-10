#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.choices import Choices
from lck.django.common.models import TimeTrackable

from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.cmdb.models import CI


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

    You must implement in subclass:
        - status field
        - synchronize_status(new_status) method

    If implementing attribute change, please do something like this:

    class AttributeChange(Auditable):
        object = ...
        new_attribute =  ..
        old_attribute = ...

    """
    user = models.ForeignKey('auth.User', verbose_name=_("user"), null=True,
           blank=True, default=None, on_delete=models.SET_NULL)
    status_lastchanged = models.DateTimeField(default=datetime.now,
            verbose_name=_("date"))
    issue_key = models.CharField(verbose_name=_("external ticket key number"),
            max_length=30, blank=True, null=True, default=None)

    class Meta:
        abstract = True

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
        pass

    def set_status_and_sync(self, new_status):
        self.status = new_status
        self.status_lastchanged = datetime.now()
        self.synchronize_status(new_status)
        self.save()

    def transition_issue(self, transition_id, retry_count=1):
        tracker = IssueTracker()
        tracker.transition_issue(
            issue_key=self.issue_key,
            transition_id=transition_id,
        )

    def create_issue(self, params, default_assignee, retry_count=1):
        """
        We create 2 IssueTracker requests for IssueTracker here.
        1) Check if assignee exists in IssueTracker
        2) Create issue with back-link for acceptance
        """
        s = settings.ISSUETRACKERS['default']['OPA']
        template=s['TEMPLATE']
        issue_type=s['ISSUETYPE']
        tracker = IssueTracker()
        ci = None
        try:
            if params.get('ci_uid'):
                ci = CI.objects.get(uid=params.get('ci_uid'))
        except CI.DoesNotExist:
            pass
        if not tracker.user_exists(params.get('technical_assignee')):
            tuser = default_assignee
        else:
            tuser = params.get('technical_assignee')
        if not tracker.user_exists(params.get('business_assignee')):
            buser = default_assignee
        else:
            buser = params.get('business_assignee')
        issue = tracker.create_issue(
                issue_type=issue_type,
                description=params.get('description'),
                summary=params.get('summary'),
                ci=ci,
                assignee=default_assignee,
                technical_assignee=tuser,
                business_assignee=buser,
                start=self.created.isoformat(),
                end='',
                template=template,
        )
        self.issue_key = issue.get('key')
        self.save()


