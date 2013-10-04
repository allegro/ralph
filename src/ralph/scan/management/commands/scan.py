#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import time
import sys
import json
from optparse import make_option

import ipaddr

from django.core.management.base import BaseCommand

from ralph.scan.manual import (
    scan_address,
)


def print_job_messages(job, last_message):
    messages = job.meta.get('messages', [])
    for address, plugin, status, message in messages[last_message:]:
        print('%s(%s): %s' % (plugin, address, message), file=sys.stderr)
    return len(messages)


class Command(BaseCommand):
    """
    Runs a manual scan of an address.
    """

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '--plugins',
            dest='plugins',
            default=None,
            help='Run only the selected plugins. Works only in interactive'
                 ' mode.'),
    )

    requires_model_validation = False

    def handle(self, *args, **kwargs):
        if not args:
            raise SystemExit("Please specify the addresses to scan.")
        try:
            addresses = [str(ipaddr.IPAddress(ip)) for ip in args]
        except ValueError as e:
            raise SystemExit(e)
        plugins = [
            'ralph.scan.plugins.snmp_macs',
            'ralph.scan.plugins.snmp_f5',
            'ralph.scan.plugins.idrac',
            'ralph.scan.plugins.ssh_linux',
            'ralph.scan.plugins.puppet',
            'ralph.scan.plugins.ssh_ibm_bladecenter',
            'ralph.scan.plugins.hp_oa',
            'ralph.scan.plugins.ssh_cisco_asa',
            'ralph.scan.plugins.ssh_cisco_catalyst',
            'ralph.scan.plugins.ipmi',
            'ralph.scan.plugins.http_supermicro',
            'ralph.scan.plugins.ilo_hp',
            'ralph.scan.plugins.ssh_cisco_asa',
            'ralph.scan.plugins.ssh_cisco_catalyst',
            'ralph.scan.plugins.ssh_proxmox',
            'ralph.scan.plugins.ssh_3par',
            'ralph.scan.plugins.ssh_ssg',
            'ralph.scan.plugins.ssh_ganeti',
            'ralph.scan.plugins.ssh_xen',
            'ralph.scan.plugins.ssh_aix',
            'ralph.scan.plugins.ssh_onstor',
            'ralph.scan.plugins.http_ibm_system_x',
            'ralph.scan.plugins.ssh_hp_p2000',
            'ralph.scan.plugins.ssh_hp_msa',
            'ralph.scan.plugins.software',
        ]
        if kwargs["plugins"]:
            new_plugins = map(lambda s: 'ralph.scan.plugins.{}'.format(s),
                kwargs["plugins"].split(","),
            )
            plugins = filter(lambda plug: plug in new_plugins, plugins)
        last_message = 0
        for address in addresses:
            job = scan_address(address, plugins)
            while not job.is_finished:
                job.refresh()
                print('Progress: %d/%d plugins' %
                      (len(job.meta.get('finished', [])), len(plugins)))
                last_message = print_job_messages(job, last_message)
                if job.is_failed:
                    raise SystemExit(job.exc_info)
                time.sleep(5)
            last_message = print_job_messages(job, last_message)
            print(json.dumps(job.result))
