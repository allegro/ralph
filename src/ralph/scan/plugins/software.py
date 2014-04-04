# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.scan.plugins import get_base_result_template
from ralph.util import network


def _detect_software(ip_address, http_family):
    software = []
    if network.check_tcp_port(ip_address, 1521):
        software.append({
            'path': 'oracle',
            'model_name': 'Oracle',
        })
    if network.check_tcp_port(ip_address, 3306):
        software.append({
            'path': 'mysql',
            'model_name': 'MySQL',
        })
    if any((
        network.check_tcp_port(ip_address, 80),
        network.check_tcp_port(ip_address, 443),
    )):
        soft = {
            'path': 'www',
            'model_name': 'WWW',
        }
        if http_family:
            soft['label'] = http_family
        software.append(soft)
    return software


def scan_address(ip_address, **kwargs):
    http_family = kwargs.get('http_family', '') or ''
    messages = []
    result = get_base_result_template('software', messages)
    result['status'] = 'success'
    software = _detect_software(ip_address, http_family)
    if software:
        result['installed_software'] = software
    return result
