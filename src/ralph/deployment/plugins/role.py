#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.deployment.models import Deployment


@plugin.register(chain='deployment', requires=['ticket'], priority=0)
def role(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    deployment.device.venture = deployment.venture
    deployment.device.venture_role = deployment.venture_role
    deployment.device.save(priority=200)
    return True
