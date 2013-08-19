# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime


def scan_address(address, **kwargs):
    messages = []
    return {
        'status': 'success',
        'plugin': 'test2',
        'date': datetime.date.today().strftime('%Y-%m-%d'),
        'messages': messages,
        'device': {
            'serial_number': '123abc',
            'mac_addresses': ['BEEFDEADCAFE'],
            'management_ip_addresses': [address],
            'processors': [
                {
                    'family': 'xeon',
                },
                {
                    'family': 'xeon',
                },
            ],
            'memory': [
                {
                    'size': 128000,
                },
                {
                    'size': 128000,
                },
                {
                    'size': 128000,
                },
                {
                    'size': 128000,
                },
            ],
            'disks': [
                {
                    'model': 'toshiba',
                    'size': 666,
                    'serial_number': 'XXXX1',
                },
                {
                    'model': 'toshiba',
                    'size': 123,
                },
            ],
        },
    }
