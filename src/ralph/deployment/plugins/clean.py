# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from lck.django.common import nested_commit_on_success

from ralph.util import plugin
from ralph.deployment.models import Deployment, DeploymentStatus
from ralph.discovery.models import IPAddress
from ralph.dnsedit.util import (
    clean_dns_entries,
    clean_dhcp_mac,
    clean_dhcp_ip,
)


@nested_commit_on_success
def do_clean(dev, user):
    # Reset save priorities
    dev.save_priorities = ''
    dev.max_save_priority = 0
    dev.save()
    # Set comment and user here, so that all changes have it
    save_comment = "Deployment"
    dev.save_comment = save_comment
    dev.save_user = user
    # Disconnect all IP addresses and delete DNS and DHCP entries
    for ipaddress in dev.ipaddress_set.all():
        clean_dhcp_ip(ipaddress.address)
        clean_dns_entries(ipaddress.address)
        ipaddress.device = None
        ipaddress.save()
    for ethernet in dev.ethernet_set.all():
        clean_dhcp_mac(ethernet.mac)
    # Delete all software components
    for c in dev.software_set.all():
        c.delete()
    for c in dev.operatingsystem_set.all():
        c.delete()
    # Disconnect all children
    for d in dev.child_set.all():
        d.parent = None
        d.save_priorities = ''
        d.max_save_priority = 0
        d.save_comment = save_comment
        d.save(user=user)
    # Delete all disk share mounts
    for m in dev.disksharemount_set.all():
        m.delete()
    for m in dev.servermount_set.all():
        m.delete()
    # Delete all disk shares
    for ds in dev.diskshare_set.all():
        ds.delete()
    # Reset uptime
    dev.uptime_seconds = 0
    dev.uptime_timestamp = None
    # Set verified, undelete, and update remarks
    dev.verified = True
    dev.deleted = False
    if dev.remarks:
        remark = "-- Remarks below are for old role %s/%s from %s --\n" % (
            dev.venture.name if dev.venture else '-',
            dev.venture_role.full_name if dev.venture_role else '-',
            datetime.date.today().strftime('%Y-%m-%d'),
        )
        dev.remarks = remark + dev.remarks
    dev.save()


@plugin.register(chain='deployment', requires=[], priority=1000)
def clean(deployment_id):
    """Prepare an existing device for deployment by cleaning old information."""
    deployment = Deployment.objects.get(id=deployment_id)
    if deployment.status != DeploymentStatus.open:
        return True
    do_clean(deployment.device, deployment.user)
    ip, created = IPAddress.concurrent_get_or_create(address=deployment.ip)
    ip.device = deployment.device
    ip.hostname = deployment.hostname
    ip.save()
    return True
