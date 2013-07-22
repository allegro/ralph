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

import ipaddr
import pprint
from django.core.management.base import BaseCommand

from ralph.scan.manual import (
    scan_address,
)


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
        plugins = ['ralph.scan.plugins.snmp_macs']
        for address in addresses:
            job = scan_address(address, plugins)
            while job.result is None:
                time.sleep(5)
            pprint.pprint(job.result)
