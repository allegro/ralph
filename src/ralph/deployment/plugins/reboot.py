#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.util import plugin
from ralph.discovery.plugins.ssh_ibm_bladecenter import ssh_ibm_reboot
from ralph.discovery.plugins.ipmi import ipmi_reboot
from ralph.discovery.hp_ilo import IloHost
from ralph.deployment.models import Deployment, DeploymentStatus


@plugin.register(chain='deployment',
                 requires=['dns', 'dhcp', 'role'],
                 priority=0)
def reboot(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    if deployment.status == DeploymentStatus.done:
        # Deployment chain requires status to be in_progress or open only.
        # But before running script assure status didn't change
        # in meantime.
        return False
    _in_progress(deployment)
    management = deployment.device.find_management()
    user, password = settings.ILO_USER, settings.ILO_PASSWORD
    if user:
        return IloHost(management, user, password).reboot(True)
    user, password = settings.IPMI_USER, settings.IPMI_PASSWORD
    if user:
        return ipmi_reboot(management, user, password, True)
    user = settings.SSH_IBM_USER
    bay = deployment.device.chassis_position
    if user and bay:
        return ssh_ibm_reboot(management, bay)
    return False


def _in_progress(deployment):
    """Change deployment status to in_progress and returns True

    Just before sending reboot command we set in_progress status.  Then, we do
    nothing more until python script from inside fresh target machine changes
    REST deployment resource  to 'done'.
    """
    deployment.status = DeploymentStatus.in_progress
    deployment.save()
    return True

