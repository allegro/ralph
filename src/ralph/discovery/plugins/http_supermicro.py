#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib2
import re
import json
import ssl

from lck.django.common import nested_commit_on_success
from ralph.util import plugin, Eth
from ralph.discovery.models import IPAddress, Device, DeviceType
from django.conf import settings


IPMI_USER = settings.IPMI_USER
IPMI_PASSWORD = settings.IPMI_PASSWORD


class Error(Exception):
    pass


class ResponseError(Error):
    pass


def _get_code(response, regexp):
    lines = []
    for line in response.readlines():
        sline = line.strip()
        if not sline or sline.startswith('//'):
            continue
        lines.append(sline)
    response = ''.join(lines)
    m = regexp.search(response)
    if not m:
        raise ResponseError("No lines match regexp {} in response {}".format(
            regexp.pattern, response))
    return m.group(1)


def _get_macs(ip):
    login_url = "https://%s/rpc/WEBSES/create.asp" % ip
    login_data = "WEBVAR_USERNAME=%s&WEBVAR_PASSWORD=%s" % (IPMI_USER,
                                                            IPMI_PASSWORD)
    session_re = re.compile(r"'SESSION_COOKIE'\s*:\s*'([^']*)'")
    mac_url = 'https://%s/rpc/getmbmac.asp' % ip
    mgmt_mac_url = 'https://%s/rpc/getnwconfig.asp' % ip
    mac_re = re.compile(r"WEBVAR_STRUCTNAME_GETMBMAC\s*:\s*\[({[^\}]*})")
    mgmt_mac_re = re.compile(
        r"WEBVAR_STRUCTNAME_HL_GETLANCONFIG\s*:\s*\[({[^\}]*})")
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    session = _get_code(opener.open(request, timeout=5), session_re)
    request = urllib2.Request(mac_url,
                              headers={'Cookie': 'SessionCookie=%s' % session})
    json_data = _get_code(opener.open(request, timeout=5),
                          mac_re).replace("'", '"')
    macs = json.loads(json_data)
    request = urllib2.Request(mgmt_mac_url,
                              headers={'Cookie': 'SessionCookie=%s' % session})
    json_data = _get_code(opener.open(request, timeout=5),
                          mgmt_mac_re).replace("'", '"')
    macs['IPMI MC'] = json.loads(json_data)['MAC']
    return macs


@nested_commit_on_success
def run_http(ip):
    macs = _get_macs(ip)
    ethernets = [Eth(label=label, mac=mac, speed=0)
                 for (label, mac) in macs.iteritems()]
    ipaddr = IPAddress.objects.get(address=ip)
    dev = Device.create(ethernets=ethernets,
                        model_name='Unknown Supermicro',
                        model_type=DeviceType.unknown)
    ipaddr.device = dev
    ipaddr.save()
    return ', '.join(macs.values())


@plugin.register(chain='discovery', requires=['http'], priority=201)
def http_supermicro(**kwargs):
    if kwargs.get('http_family', '') not in ('Thomas-Krenn',):
        return False, 'no match.', kwargs
    ip = str(kwargs['ip'])
    try:
        macs = run_http(ip)
    except urllib2.URLError as e:
        message = 'Error %s: %s' % (
            getattr(e, 'code', ''), getattr(e, 'reason', ''))
        return False, message, kwargs
    except (Error, ssl.SSLError) as e:
        return False, str(e), kwargs
    return True, macs, kwargs
