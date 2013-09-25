# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ilo_hp', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append('Not configured.')
    else:
        pass
    return result

