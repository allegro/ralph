# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.scan.errors import (
    ConnectionError,
    NoMatchError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util.network import check_tcp_port, connect_ssh


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _connect_ssh(ip_address, user, password):
    if not check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a Juniper switch.')
    return connect_ssh(ip_address, user, password)


def _ssh_juniper(ssh):
    pass


def scan_address(ip_address, **kwargs):
    http_family = kwargs.get('http_family', '')
    if http_family and http_family.strip().lower() not in ('juniper',):
        raise NoMatchError('It is not Juniper.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_juniper', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_SSG_USER and SSH_SSG_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            ssh = _connect_ssh(ip_address, user, password)
        except ConnectionError as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            try:
                device_info = _ssh_juniper(ssh)
            finally:
                ssh.close()
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
