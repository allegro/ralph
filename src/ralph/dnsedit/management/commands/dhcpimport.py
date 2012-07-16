#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

import iscconf

from django.core.management.base import BaseCommand
from django.conf import settings

from ralph.dnsedit.models import DHCPEntry
from lck.django.common.models import MACAddressField

class Command(BaseCommand):
    """Import DHCP config"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, filename, *args, **options):
        data = iscconf.parse(open(filename, 'r').read())
        for key, info in data.iteritems():
            if not key[0] == 'host':
                continue
            mac = MACAddressField.normalize(info[('hardware', 'ethernet')])
            for entry in DHCPEntry.objects.filter(mac=mac):
                entry.delete()
            addresses = info[('fixed-address',)]
            if not isinstance(addresses, list):
                addresses = [addresses]
            for address in addresses:
                print('Importing %s = %s' % (address, mac))
                entry = DHCPEntry(ip=address.strip(), mac=mac)
                entry.save()

