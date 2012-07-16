#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

import dns.zone
import dns.rdatatype

from django.core.management.base import BaseCommand
from django.conf import settings

from powerdns.models import Domain, Record


class Command(BaseCommand):
    """Import DNS config"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, filename, *args, **options):
        zone = dns.zone.from_file(filename)
        domain = Domain(name=str(zone.origin).strip('.'), type='MASTER')
        domain.save()
        for entry in zone:
            node = zone[entry]
            name = str(entry.choose_relativity(zone.origin, False)).strip('.')
            for rdataset in node:
                qtype = dns.rdatatype.to_text(rdataset.rdtype)
                ttl = rdataset.ttl
                for rdata in rdataset:
                    prio = None
                    if qtype == 'MX':
                        prio = rdata.preference
                        content = str(rdata.exchange.choose_relativity(
                                        zone.origin, False))
                    elif qtype == 'TXT':
                        content = b'\n'.join(rdata.strings)
                    elif qtype == 'CNAME':
                        content = rdata.to_text(zone.origin, False).strip('.')
                    else:
                        content = rdata.to_text(zone.origin, False)
                    record = Record(
                        domain=domain,
                        name=name,
                        type=qtype,
                        ttl=ttl,
                        prio=prio,
                        content=content,
                    )
                    record.save()
