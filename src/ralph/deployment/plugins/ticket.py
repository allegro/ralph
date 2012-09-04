#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.deployment.models import DeploymentStatus, Deployment


@plugin.register(chain='deployment', requires=[], priority=100)
def ticket(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    issue_tracker = IssueTracker()
    if not deployment.issue_key:
        deployment.create_issue()
        # prevent other plugins to be executed until issue fires.
        return False
    if issue_tracker.deployment_accepted(deployment):
        deployment.set_status_and_sync(DeploymentStatus.in_progress.id)
        deployment.set_status_and_sync(DeploymentStatus.in_deployment.id)
        return True
    return False
