# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
import datetime


def scan_address(address, **kwargs):
    time.sleep(4)
    messages = []
    messages.append("Testing plugin number one.")
    return {
        'status': 'success',
        'plugin': 'test1',
        'date': datetime.date.today().strftime('%Y-%m-%d'),
        'messages': messages,
        'device': {
            'serial_number': '123abc',
            'mac_addresses': ['00C0B7D28588'],
            'management_ip_addresses': [address],
        },
    }
