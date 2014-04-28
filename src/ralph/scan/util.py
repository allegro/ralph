# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

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
        scan_summary.previous_checksum = job.meta.get(
            'results_checksum',
        )
        scan_summary.false_positive_checksum = None
        scan_summary.save()
        job.meta['changed'] = False
        job.save()
