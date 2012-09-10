#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.util import plugin
from ralph .discovery.plugins.ssh_ibm_bladecenter import ssh_ibm_reboot
from ralph.discovery.plugins.ipmi import ipmi_reboot
from ralph.discovery.hp_ilo import IloHost
from ralph.deployment.models import Deployment


@plugin.register(chain='deployment',
                 requires=['ticket', 'dns', 'dhcp', 'puppet', 'role'],
                 priority=0)
def reboot(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    management = deployment.device.find_management()
    user, password = settings.ILO_USER, settings.ILO_PASSWORD
    if user and IloHost(management, user, password).reboot(True):
            return True
    user, password = settings.IPMI_USER, settings.IPMI_PASSWORD
    if user and ipmi_reboot(management, user, password, True):
        return True
    user = settings.SSH_IBM_USER
    bay = deployment.device.chassis_position
    if user and bay and ssh_ibm_reboot(management, bay):
        return True
    return False
