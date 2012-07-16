#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand
from django.conf import settings

from ralph.dnsedit.models import DHCPEntry


class Command(BaseCommand):
    """Update the billing data from OpenStack"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for macaddr, in DHCPEntry.objects.values_list('mac').distinct():
            ips = []
            for ip, in DHCPEntry.objects.filter(mac=macaddr).values_list('ip'):
                ips.append(ip)
            name = ips[0]
            address = ', '.join(ips)
            mac = ':'.join('%s%s' % c for c in zip(macaddr[::2],
                                                   macaddr[1::2])).upper()
            print('host %s { fixed-address %s; hardware ethernet %s; }'
                    % (name, address, mac))
