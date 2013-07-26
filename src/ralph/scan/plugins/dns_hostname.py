# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import network
from ralph.scan.plugins import get_base_result_template


def scan_address(address, **kwargs):
    messages = []
    data = get_base_result_template('dns_hostname', messages)
    hostname = network.hostname(address)
    if hostname:
        data['device'] = {
            'hostname': hostname,
        }
        data['status'] = 'success'
    else:
        data['status'] = 'error'
    return data
