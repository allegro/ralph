# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import re
import urllib2

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.models import MAC_PREFIX_BLACKLIST
from ralph.scan.errors import Error, NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
LOGIN_URL_TEMPLATE = 'https://{ip_address}/rpc/WEBSES/create.asp'
MAC_URL_TEMPLATE = 'https://{ip_address}/rpc/getmbmac.asp'
MGMT_MAC_URL_TEMPLATE = 'https://{ip_address}/rpc/getnwconfig.asp'


def _get_code(response, regexp):
    lines = []
    for line in response.readlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        lines.append(line)
    response = ''.join(lines)
    m = regexp.search(response)
    if not m:
        raise Error('No match.')
    return m.group(1)


def _get_mac_addresses(ip_address, user, password):
    opener = urllib2.build_opener()
    request = urllib2.Request(
        LOGIN_URL_TEMPLATE.format(ip_address=ip_address),
        'WEBVAR_USERNAME={user}&WEBVAR_PASSWORD={password}'.format(
            user=user,
            password=password,
        ),
    )
    session = _get_code(
        opener.open(request, timeout=5),
        re.compile(r"'SESSION_COOKIE'\s*:\s*'([^']*)'"),
    )
    request = urllib2.Request(
        MAC_URL_TEMPLATE.format(ip_address=ip_address),
        headers={'Cookie': 'SessionCookie=%s' % session},
    )
    json_data = _get_code(
        opener.open(request, timeout=5),
        re.compile(r"WEBVAR_STRUCTNAME_GETMBMAC\s*:\s*\[({[^\}]*})"),
    ).replace("'", '"')
    macs = json.loads(json_data).values()
    request = urllib2.Request(
        MGMT_MAC_URL_TEMPLATE.format(ip_address=ip_address),
        headers={'Cookie': 'SessionCookie=%s' % session},
    )
    json_data = _get_code(
        opener.open(request, timeout=5),
        re.compile(r"WEBVAR_STRUCTNAME_HL_GETLANCONFIG\s*:\s*\[({[^\}]*})"),
    ).replace("'", '"')
    macs.append(json.loads(json_data)['MAC'])
    return [
        MACAddressField.normalize(mac)
        for mac in macs
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST
    ]


def _http_supermicro(ip_address, user, password):
    device_info = {
        'management_ip_addresses': [ip_address],
    }
    macs = _get_mac_addresses(ip_address, user, password)
    if macs:
        device_info['mac_addresses'] = macs
    return device_info


def scan_address(ip_address, **kwargs):
    if kwargs.get('http_family', '') not in ('Thomas-Krenn',):
        raise NoMatchError('It is not Thomas-Krenn.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('http_supermicro', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append('Not configured.')
    else:
        try:
            device_info = _http_supermicro(ip_address, user, password)
        except Error as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
