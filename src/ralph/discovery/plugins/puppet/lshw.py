#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import zlib

from lck.django.common import nested_commit_on_success


from .facts import handle_facts_ethernets
from .util import assign_ips
from ralph.discovery import lshw
from ralph.discovery.models import SERIAL_BLACKLIST

SAVE_PRIORITY = 53


@nested_commit_on_success
def parse_lshw(data, facts, is_virtual):
    try:
        data = zlib.decompress(data)
    except zlib.error:
        return False, "lshw decompression error."
    sn = facts.get('serialnumber') # use a Puppet fact because lshw gives
                                   # wrong serial numbers
    if sn in SERIAL_BLACKLIST:
        sn = None
    try:
        dev = lshw.handle_lshw(data, is_virtual, sn, SAVE_PRIORITY)
    except lshw.Error as e:
        return False, unicode(e)
    ip_addresses, ethernets_facts = handle_facts_ethernets(facts)
    assign_ips(dev, ip_addresses)
    return dev, dev.model.name

