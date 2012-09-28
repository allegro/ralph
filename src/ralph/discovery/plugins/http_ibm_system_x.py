#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib2

from django.conf import settings
from xml.etree import cElementTree as ET
from lck.django.common import nested_commit_on_success

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, Processor, IPAddress,
                                    ComponentModel, ComponentType, Memory)
from ralph.discovery.plugins.http import guess_family, get_http_info


USER = settings.IBM_SYSTEM_X_USER
PASSWORD = settings.IBM_SYSTEM_X_PASSWORD
SAVE_PRIORITY = 5

# WSDL module from IBM System X management is generally broken,
# so we prepare SOAP requests by hand

GENERIC_SOAP_TEMPLATE = '''
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
</SOAP-ENV:Envelope>'''


class Error(Exception):
    pass


def _send_soap(post_url, session_id, message):
    opener = urllib2.build_opener()
    request = urllib2.Request(
        post_url, message,
        headers={'session_id': session_id}
    )
    response = opener.open(request, timeout=10)
    response_data = response.read()
    return response_data


def get_session_id(ip):
    login_url = "http://%s/session/create" % ip
    login_data = "%s,%s" % (USER, PASSWORD)
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    response = opener.open(request, timeout=15)
    response_data = response.readlines()
    if response_data and response_data[0][:2] == 'ok':
        return response_data[0][3:]
    raise Error('Session error')


def get_model_name(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData',
        resource='Monitors',
        body='''
        <GetVitalProductData xmlns="http://www.ibm.com/iBMC/sp/Monitors"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        </GetVitalProductData>'''
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    product_name = tree.findall(
        '{0}Body/GetVitalProductDataResponse/'
        'GetVitalProductDataResponse/MachineLevelVPD/'
        'ProductName'.format('{http://www.w3.org/2003/05/soap-envelope}'))
    return product_name[0].text


def get_sn(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings',
        resource='iBMCControl',
        body='''
        <GetSPNameSettings xmlns="http://www.ibm.com/iBMC/sp/iBMCControl"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetSPNameSettings>'''
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    sn = tree.findall('{0}Body/GetSPNameSettingsResponse/SPName'.format(
        '{http://www.w3.org/2003/05/soap-envelope}'))
    sn = sn[0].text
    return sn


def get_memory(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetMemoryInfo',
        resource='Monitors',
        body='''
        <GetMemoryInfo xmlns="http://www.ibm.com/iBMC/sp/Monitors"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetMemoryInfo>
    ''')
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    mems = []
    memory = tree.findall('{0}Body/GetMemoryInfoResponse/Memory/*'.format(
        '{http://www.w3.org/2003/05/soap-envelope}'))
    for record in memory:
        mems.append(dict(
            label=record.find('Description').text,
            index=int(record.find('Description').text.split()[1]),
            size=int(record.find('Size').text) * 1024,
        ))
    return mems


def get_processors(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        resource='Monitors',
        action='http://www.ibm.com/iBMC/sp/Monitors/GetProcessorInfo',
        body='''
        <GetProcessorInfo xmlns="http://www.ibm.com/iBMC/sp/Monitors"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetProcessorInfo>
        '''
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    data = tree.findall('{0}Body/GetProcessorInfoResponse/Processor/*'.format(
        '{http://www.w3.org/2003/05/soap-envelope}'))
    processors = []
    for d in data:
        dsc = d.find('Description').text
        speed = d.find('Speed').text
        family = d.find('Family').text
        cores = d.find('Cores').text
        threads = d.find('Threads').text
        index = dsc.split()[1]
        label = '%(family)s CPU %(speed)s MHz, %(cores)s cores %(threads)s threads' % dict(
            family=family,
            speed=speed,
            cores=cores,
            threads=threads,
        )
        processors.append(dict(
            index=index,
            label=label,
            speed=speed,
            cores=cores,
            family=family,
        ))
    return processors


def get_mac_addresses(management_url, session_id):
    message = GENERIC_SOAP_TEMPLATE % dict(
        management_url=management_url,
        action='http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses',
        resource='Monitors',
        body='''
    <GetHostMacAddresses xmlns="http://www.ibm.com/iBMC/sp/Monitors"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetHostMacAddresses>
    ''')
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    mac_addresses = tree.findall(
        '{0}Body/GetHostMacAddressesResponse/**'.format(
        '{http://www.w3.org/2003/05/soap-envelope}')
    )
    macs = []
    for mac in mac_addresses:
        dsc = mac.find('Description').text
        add = mac.find('Address').text
        macs.append([dsc, add])
    return macs


@nested_commit_on_success
def run_http_ibm_system_x(ip):
    session_id = get_session_id(ip)
    management_url = "http://%s/wsman" % ip
    model_name = get_model_name(management_url, session_id)
    sn = get_sn(management_url, session_id)
    macs = get_mac_addresses(management_url, session_id)
    ethernets = [Eth(label=label, mac=mac, speed=0)
                 for (label, mac) in macs]
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.is_management = True
    ipaddr.save()
    dev = Device.create(
        ethernets=ethernets,
        model_name=model_name,
        sn=sn,
        model_type=DeviceType.rack_server,
    )
    dev.management = ipaddr
    dev.save(priority=SAVE_PRIORITY)
    ipaddr.device = dev
    ipaddr.save()
    detected_memory = get_memory(management_url, session_id)
    detected_memory_indexes = [x.get('index') for x in detected_memory]
    for m in dev.memory_set.exclude(index__in=detected_memory_indexes):
        m.delete()
    for m in detected_memory:
        index = m['index']
        mem, _ = Memory.concurrent_get_or_create(index=index, device=dev)
        mem.label = m['label']
        mem.size = m['size']
        mem.save(priority=SAVE_PRIORITY)
        mem.model, c = ComponentModel.concurrent_get_or_create(
            name='RAM %s %dMiB' % (mem.label, mem.size), size=mem.size,
            type=ComponentType.memory.id,
            family=mem.label, cores=0
        )
        mem.save(priority=SAVE_PRIORITY)
    detected_processors = get_processors(management_url, session_id)
    detected_processors_keys = [x.get('index') for x in detected_processors]
    for cpu in dev.processor_set.exclude(index__in=detected_processors_keys):
        cpu.delete()
    # add new
    for p in detected_processors:
        processor_model, _ = ComponentModel.concurrent_get_or_create(
            name=p.get('label'),
            speed=p.get('speed'),
            type=ComponentType.processor.id,
            family=p.get('family'),
            cores=p.get('cores')
        )
        processor, _ = Processor.concurrent_get_or_create(
            device=dev,
            index=p.get('index'),
        )
        processor.label = p.get('label')
        processor.model = processor_model
        processor.speed = p.get('speed')
        processor.save()
    return model_name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def http_ibm_system_x(**kwargs):
    if USER is None or PASSWORD is None:
        return False, 'no credentials.', kwargs
    ip = str(kwargs['ip'])
    try:
        headers, document = get_http_info(ip)
        family = guess_family(headers, document)
        if family != 'IBM System X':
            return False, 'not identified.', kwargs
        name = run_http_ibm_system_x(ip)
        return True, name, kwargs
    except (network.Error, Error) as e:
        return False, str(e), kwargs

