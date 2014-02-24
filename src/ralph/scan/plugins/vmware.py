# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.scan.errors import NoMatchError
from ralph.scan.plugins import get_base_result_template


def scan_address(ip_address, **kwargs):
    http_family = kwargs.get('http_family', '').strip()
    if http_family and http_family.lower() not in ('esx',):
        raise NoMatchError('It is not VMWare.')
    messages = []
    result = get_base_result_template('vmware', messages)
    return result
