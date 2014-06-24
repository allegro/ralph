# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib2

from django.conf import settings
from lck.django.common.models import MACAddressField
from xml.etree import cElementTree as ET

from ralph.discovery.http import guess_family, get_http_info
from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST
from ralph.scan.errors import (
    AuthError,
    NoMatchError,
    NotConfiguredError,
    TreeError,
)
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
GENERIC_SOAP_TEMPLATE = '''\n
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                   xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <SOAP-ENV:Header>
        <wsa:To>http://%(management_url)s</wsa:To>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsman:ResourceURI>http://www.ibm.com/iBMC/sp/%(resource)s</wsman:ResourceURI>
        <wsa:Action>%(action)s</wsa:Action>
        <wsa:MessageID>dt:1348650519402</wsa:MessageID>
    </SOAP-ENV:Header>
    <SOAP-ENV:Body>
        %(body)s
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''


def _send_soap(post_url, session_id, message):
    opener = urllib2.build_opener()
    request = urllib2.Request(
        post_url, message,
        headers={'session_id': session_id},
    )
    response = opener.open(request, timeout=10)
    response_data = response.read()
    return response_data


def _get_session_id(ip_address, user, password):
    login_url = "http://%s/session/create" % ip_address
    login_data = "%s,%s" % (user, password)
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    response = opener.open(request, timeout=15)
    response_data = response.readlines()
    if response_data and response_data[0][:2] == 'ok':
        return response_data[0][3:]
    raise AuthError('Session error.')


def _get_model_name(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData',
        resource='Monitors',
        body='''
            <GetVitalProductData xmlns="http://www.ibm.com/iBMC/sp/Monitors"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            </GetVitalProductData>
        ''',
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    product_name = tree.findall(
        '{0}Body/GetVitalProductDataResponse/'
        'GetVitalProductDataResponse/MachineLevelVPD/'
        'ProductName'.format('{http://www.w3.org/2003/05/soap-envelope}'),
    )
    try:
        return product_name[0].text
    except IndexError:
        raise TreeError(
            "Improper response. Couldn't find model name. "
            "Full response: %s" % soap_result,
        )


def _get_sn(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings',
        resource='iBMCControl',
        body='''
            <GetSPNameSettings xmlns="http://www.ibm.com/iBMC/sp/iBMCControl"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            </GetSPNameSettings>
        ''',
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    sn = tree.findall('{0}Body/GetSPNameSettingsResponse/SPName'.format(
        '{http://www.w3.org/2003/05/soap-envelope}',
    ))
    try:
        return sn[0].text
    except IndexError:
        raise TreeError(
            "Improper response. Couldn't find serial number. "
            "Full response: %s" % soap_result,
        )


def _get_mac_addresses(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses',
        resource='Monitors',
        body='''
            <GetHostMacAddresses xmlns="http://www.ibm.com/iBMC/sp/Monitors"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            </GetHostMacAddresses>
        ''',
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    mac_addresses = tree.findall(
        '{0}Body/GetHostMacAddressesResponse/**'.format(
            '{http://www.w3.org/2003/05/soap-envelope}',
        ),
    )
    return [
        MACAddressField.normalize(
            mac.find('Address').text
        ) for mac in mac_addresses
    ]


def _get_memory(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetMemoryInfo',
        resource='Monitors',
        body='''
            <GetMemoryInfo xmlns="http://www.ibm.com/iBMC/sp/Monitors"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            </GetMemoryInfo>
        ''',
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    memory = tree.findall('{0}Body/GetMemoryInfoResponse/Memory/*'.format(
        '{http://www.w3.org/2003/05/soap-envelope}',
    ))
    return [
        dict(
            label=chip.find('Description').text,
            index=int(chip.find('Description').text.split()[1]),
            size=int(chip.find('Size').text) * 1024,
        ) for chip in memory
    ]


def _get_processors(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        resource='Monitors',
        action='http://www.ibm.com/iBMC/sp/Monitors/GetProcessorInfo',
        body='''
            <GetProcessorInfo xmlns="http://www.ibm.com/iBMC/sp/Monitors"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            </GetProcessorInfo>
        ''',
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    data = tree.findall('{0}Body/GetProcessorInfoResponse/Processor/*'.format(
        '{http://www.w3.org/2003/05/soap-envelope}',
    ))
    processors = []
    for d in data:
        dsc = d.find('Description').text
        speed = d.find('Speed').text
        family = d.find('Family').text
        cores = d.find('Cores').text
        threads = d.find('Threads').text
        index = dsc.split()[1]
        label = '%s CPU %s MHz, %s cores %s threads' % (
            family,
            speed,
            cores,
            threads,
        )
        processors.append(dict(
            index=index,
            label=label,
            speed=speed,
            cores=cores,
            family=family,
        ))
    return processors


def _http_ibm_system_x(ip_address, user, password):
    session_id = _get_session_id(ip_address, user, password)
    management_url = "http://%s/wsman" % ip_address
    model_name = _get_model_name(management_url, session_id)
    sn = _get_sn(management_url, session_id)
    device = {
        'type': DeviceType.rack_server.raw,
        'model_name': model_name,
        'management_ip_address': [ip_address],
    }
    if sn not in SERIAL_BLACKLIST:
        device['serial_number'] = sn
    macs = _get_mac_addresses(management_url, session_id)
    if macs:
        device['mac_addresses'] = macs
    memory = _get_memory(management_url, session_id)
    if memory:
        device['memory'] = memory
    processors = _get_processors(management_url, session_id)
    if processors:
        device['processors'] = processors
    return device


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
    result.update({
        'status': 'success',
        'device': _http_ibm_system_x(ip_address, user, password),
    })
    return result
