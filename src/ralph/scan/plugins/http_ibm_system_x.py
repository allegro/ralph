# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib2

from django.conf import settings

from ralph.discovery.http import guess_family, get_http_info
from ralph.scan.errors import Error, NotConfiguredError, NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def get_session_id(ip_address, user, password):
    login_url = "http://%s/session/create" % ip_address
    login_data = "%s,%s" % (user, password)
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    response = opener.open(request, timeout=15)
    response_data = response.readlines()
    if response_data and response_data[0][:2] == 'ok':
        return response_data[0][3:]
    raise Error('Session error.')


def _http_ibm_system_x(ip_address, user, password):
    session_id = get_session_id(ip_address)
    management_url = "http://%s/wsman" % ip_address
    model_name = get_model_name(management_url, session_id)


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('http_ibm_system_x', messages)
    if not user or not password:
        raise NotConfiguredError(
            'Not configured. Set IBM_SYSTEM_X_USER and IBM_SYSTEM_X_PASSWORD '
            'in your configuration file.',
        )
    headers, document = get_http_info(ip_address)
    family = guess_family(headers, document)
    if family != 'IBM System X':
        raise NoMatchError('It is not IBM System X device.')
    try:
        device_info = _http_ibm_system_x(ip_address, user, password)
    except Error as e:
        result['status'] = 'error'
        messages.append(unicode(e))
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result

