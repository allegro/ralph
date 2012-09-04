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
    import pdb; pdb.set_trace()
    deployment = Deployment.objects.get(id=deployment_id)
    issue_tracker = IssueTracker()
    if not deployment.issue_key:
        deployment.fire_issue()
        # prevent other plugins to be executed until issue fires.
        return False
    if issue_tracker.deployment_accepted(deployment):
        deployment.status = DeploymentStatus.in_progress.id
        deployment.save()
        obj_id = deployment.id
        x = Deployment.objects.get(id=obj_id)
        x.status = DeploymentStatus.in_deployment.id
        x.save()
        return True
    return False
