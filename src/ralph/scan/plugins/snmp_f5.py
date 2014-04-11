# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST
from ralph.discovery.snmp import snmp_command
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class Error(Exception):
    pass


def _snmp_f5(ip_address, snmp_name, snmp_community):
    if '.f5app' not in snmp_name:
        raise Error('The SNMP name `%s` is not supported by this plugin.' % (
            snmp_name,
        ))
    try:
        model = str(
            snmp_command(
                ip_address,
                snmp_community,
                [int(i) for i in '1.3.6.1.4.1.3375.2.1.3.5.2.0'.split('.')],
                attempts=1,
                timeout=0.5,
            )[0][1],
        )
        sn = str(
            snmp_command(
                ip_address,
                snmp_community,
                [int(i) for i in '1.3.6.1.4.1.3375.2.1.3.3.3.0'.split('.')],
                attempts=1,
                timeout=0.5,
            )[0][1],
        )
    except TypeError:
        raise Error('No answer.')
    except IndexError:
        raise Error('Incorrect answer.')
    result = {
        'type': str(DeviceType.load_balancer),
        'model_name': 'F5 %s' % model,
    }
    if sn not in SERIAL_BLACKLIST:
        result['serial_number'] = sn
    return result


def scan_address(ip_address, **kwargs):
    snmp_name = kwargs.get('snmp_name', '') or ''
    snmp_version = kwargs.get('snmp_version', '2c') or '2c'
    if snmp_version == '3':
        snmp_community = SETTINGS['snmp_v3_auth']
    else:
        snmp_community = str(kwargs['snmp_community'])
    messages = []
    result = get_base_result_template('snmp_f5', messages)
    try:
        device_info = _snmp_f5(
            ip_address,
            snmp_name,
            snmp_community,
        )
    except Error as e:
        messages.append(unicode(e))
        result.update(status="error")
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result
