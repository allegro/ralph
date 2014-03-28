#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery.plugins.ssh_ibm_bladecenter import ssh_ibm_reboot
from ralph.discovery.plugins.ipmi import ipmi_reboot
from ralph.discovery.hp_ilo import IloHost
from ralph.deployment.models import Deployment, DeploymentStatus


# This plugin is temporarily disabled.
def reboot(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    if deployment.status == DeploymentStatus.done:
        # Deployment chain requires status to be in_progress or open only.
        # But before running script assure status didn't change
        # in meantime.
        return False
    management = deployment.device.find_management()
    if not management:
        return True
    management_ip = management.address
    user, password = settings.ILO_USER, settings.ILO_PASSWORD
    if user and IloHost(management_ip, user, password).reboot(True):
        return True
    user, password = settings.IPMI_USER, settings.IPMI_PASSWORD
    if user and ipmi_reboot(management_ip, user, password, True):
        return True
    user = settings.SSH_IBM_USER
    bay = deployment.device.chassis_position
    if user and bay:
        ssh_ibm_reboot(management_ip, bay)
    return True
