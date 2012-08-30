#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from ralph.cmdb.integration.issuetracker import IssueTracker

from ralph.deployment.models import (DeploymentStatus, Deployment,
        deployment_accepted)


class JiraRSS(object):
    def __init__(self):
        settings.BUGTRACKER_CMDB_PROJECT #'AGS'

    def get_new_issues(self):
        return ['AGS-18553']


class JiraAcceptance(object):

    def accept_deployment(self, deployment):
        deployment_accepted.send(sender=deployment, deployment_id=deployment.id)

    def __init__(self):
        self.acceptance_status = 'accept'

    def run(self):
        b = IssueTracker()
        x = JiraRSS()
        issues = x.get_new_issues()
        for issue in issues:
            exists = True
            try:
                d = Deployment.objects.get(issue_key=issue, status = DeploymentStatus.open.id)
            except Deployment.DoesNotExist:
                exists = False
            if exists and d.status == DeploymentStatus.opened.id:
                jira_issue = b.find_issue(params=({'key' : issue}))
                import pdb; pdb.set_trace()
                if jira_issue.get('status') == self.acceptance_status:
                    self.accept_deployment(issue)
