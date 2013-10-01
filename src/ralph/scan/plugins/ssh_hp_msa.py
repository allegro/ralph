# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.errors import (
    ConnectionError,
    NoMatchError,
    NotConfiguredError,
)
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _ssh_hp_msa(ip_address, user, password):
    pass


def scan_address(ip_address, **kwargs):
    if kwargs.get('http_family') not in ('WindRiver-WebServer',):
        raise NoMatchError("It's not a HP MSA Storage.")
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        raise NoMatchError("Incompatible Nexus found.")
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_hp_msa', messages)
    if not user or not password:
        raise NotConfiguredError(
            'Not configured. Set SSH_MSA_USER and SSH_MSA_PASSWORD in '
            'your configuration file.',
        )
    try:
        device_info = _ssh_hp_msa(ip_address, user, password)
    except ConnectionError as e:
        result['status'] = 'error'
        messages.append(unicode(e))
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result

