#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.dnsedit.models import DHCPEntry, DHCPServer
from ralph.dnsedit.util import reset_dhcp
from ralph.deployment.models import Deployment


@plugin.register(chain='deployment', requires=['dns'], priority=0)
def dhcp(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    try:
        entry = DHCPEntry.objects.get(ip=deployment.ip, mac=deployment.mac)
    except DHCPEntry.DoesNotExist:
        reset_dhcp(deployment.ip, deployment.mac)
    else:
        # Check that all DHCP servers already have this entry.
        servers = DHCPServer.objects.all()
        if not servers.count():
            return False
        for server in servers:
            if entry.created > server.last_synchronized:
                return False
        return True
    return False
