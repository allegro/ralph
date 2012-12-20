#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.dnsedit.util import reset_dns
from ralph.deployment.models import Deployment
from ralph.discovery.models import IPAddress


@plugin.register(chain='deployment', requires=['ticket'], priority=0)
def dns(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    reset_dns(deployment.hostname, deployment.ip)
    ipaddr, created = IPAddress.objects.concurrent_get_or_create(
        address=deployment.ip
    )
    if created:
        ipaddr.hostname = deployment.hostname
    ipaddr.device = deployment.device
    ipaddr.save()
    return True
