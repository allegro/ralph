#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.deployment.models import Deployment, DeploymentStatus
from ralph.util import plugin


@plugin.register(chain='deployment',
                 requires=['dns', 'dhcp', 'role'],
                 priority=0)
def change_status(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    deployment.status = DeploymentStatus.in_progress
    deployment.save()
    return True
