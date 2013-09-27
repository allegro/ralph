# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class Error(Exception):
    pass


class ConnectionError(Error):
    pass


def _connect_ssh(ip_address, user, password):
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a 3PAR server.')
    return network.connect_ssh(ip_address, user, password)


def _ssh_3par(ip_address, user, password):
    ssh = _connect_ssh(ip_address, user, password)
todo


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_3par', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_3PAR_USER and SSH_3PAR_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            device_info = _ssh_3par(ip_address, user, password)
        except ConnectionError as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return device_info

