#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.cmdb.integration.issuetracker_plugins.jira import (JiraAcceptance,
                                                              IntegrityError)
from ralph.deployment.models import DeploymentStatus, Deployment

@plugin.register(chain='deployment', requires=[], priority=100)
def ticket(deployment):
    try:
        if JiraAcceptance().is_deployment_accepted(deployment):
            deployment.status = DeploymentStatus.in_progress.id
            deployment.save()
            obj_id = deployment.id
            x = Deployment.objects.get(id=obj_id)
            x.status = DeploymentStatus.in_deployment.id
            x.save()
            return True
    except IntegrityError:
        pass
    return False
