#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from optparse import make_option
import textwrap
import time
import sys
import json

import ipaddr
import pprint
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
        ]
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
