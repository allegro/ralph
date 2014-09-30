# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
from collections import namedtuple

import datetime
from django.utils import timezone

from ralph.discovery.models import Network
from ralph.scan.models import ScanSummary


def find_network(network_spec):
    """Returns network object by network address."""
    try:
        address = str(ipaddr.IPNetwork(network_spec))
    except ValueError:
        network = Network.objects.get(name=network_spec)
    else:
        network = Network.objects.get(address=address)
    return network


def update_scan_summary(job):
    try:
        scan_summary = ScanSummary.objects.get(job_id=job.id)
    except ScanSummary.DoesNotExist:
        return
    else:
        scan_summary.previous_checksum = job.meta.get('results_checksum')
        scan_summary.false_positive_checksum = None
        scan_summary.save()
        job.meta['changed'] = False
        job.save()


PendingChanges = namedtuple('PendingChanges', ['new_devices', 'changed_devices'])


def get_pending_changes():
    """Return a tuple of new/edited IPs that are pending from a scan."""
    from ralph.scan.api import SCAN_RESULT_TTL
    delta = timezone.now() - datetime.timedelta(seconds=SCAN_RESULT_TTL)
    all_changes = ScanSummary.objects.filter(modified__gt=delta)
    new, changed = (
        all_changes.filter(ipaddress__device=None).count(),
        all_changes.exclude(ipaddress__device=None).count(),
    )
    return PendingChanges(new, changed)
