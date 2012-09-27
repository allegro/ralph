#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common import nested_commit_on_success
import urllib2
from xml.etree import cElementTree as ET

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, IPAddress,
                                    ComponentModel, ComponentType, Memory)
from ralph.discovery.plugins.http import  guess_family, get_http_info


try:
    USER = settings.IBM_SYSTEM_X_USER
    PASSWORD = settings.IBM_SYSTEM_X_PASSWORD
except AttributeError:
    USER = None
    PASSWORD = None

# WSDL module from IBM System X management is generally broken,
# so we prepare SOAP requests by hand

generic_soap_template = '''
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
    request = urllib2.Request(post_url, message,
          headers={'session_id': session_id}
    )
    response = opener.open(request, timeout=10)
    if response.code != 200:
        raise Error()
    response_data = response.read()
    return response_data


def _get_session_id(ip):
    login_url = "http://%s/session/create" % ip
    login_data = "%s,%s" % (USER, PASSWORD)
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    response = opener.open(request, timeout=15)
    if response.code != 200:
        raise Error()
    response_data = response.readlines()
    if response_data and response_data[0][:2] =='ok':
        return response_data[0][3:]
    raise Error()


def _get_model_name(management_url, session_id):
    message = generic_soap_template % dict(
            management_url=management_url,
            action='http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData',
            resource='Monitors',
            body='''
    <GetVitalProductData xmlns="http://www.ibm.com/iBMC/sp/Monitors"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    </GetVitalProductData>
    ''')
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    product_name = tree.findall('{0}Body/GetVitalProductDataResponse/'
            'GetVitalProductDataResponse/MachineLevelVPD/'
            'ProductName'.format('{http://www.w3.org/2003/05/soap-envelope}'))
    return product_name[0].text


def _get_sn(management_url, session_id):
    message = generic_soap_template % dict(
            management_url=management_url,
            action='http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings',
            resource='iBMCControl',
            body='''
        <GetSPNameSettings xmlns="http://www.ibm.com/iBMC/sp/iBMCControl"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetSPNameSettings>
        ''')
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    sn = tree.findall('{0}Body/GetSPNameSettingsResponse/SPName'.format(
        '{http://www.w3.org/2003/05/soap-envelope}'))
    sn = sn[0].text
    return sn


def _get_memory(management_url, session_id):
    message = generic_soap_template % dict(
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
            size=int(record.find('Size').text)*1024,
        ))
    return mems


def _get_mac_addresses(management_url, session_id):
    message = generic_soap_template % dict(
            management_url=management_url,
            action='http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses',
            resource='Monitors',
            body='''
    <GetHostMacAddresses xmlns="http://www.ibm.com/iBMC/sp/Monitors"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetHostMacAddresses>
    ''')
    soap_result = _send_soap(management_url, session_id, message)
    tree=ET.XML(soap_result)
    mac_addresses = tree.findall('{0}Body/GetHostMacAddressesResponse/**'.format(
        '{http://www.w3.org/2003/05/soap-envelope}'))
    macs = []
    for mac in mac_addresses:
        dsc = mac.find('Description').text
        add = mac.find('Address').text
        macs.append([dsc, add])
    return macs


@nested_commit_on_success
def _run_http_ibm_system_x(ip):
    session_id = _get_session_id(ip)
    management_url = "http://%s/wsman" % ip
    model_name  = _get_model_name(management_url, session_id)
    sn = _get_sn(management_url, session_id)
    macs = _get_mac_addresses(management_url, session_id)
    ethernets = [Eth(label=label, mac=mac, speed=0)
                 for (label, mac) in macs]
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.is_management = True
    ipaddr.save()
    dev = Device.create(ethernets=ethernets,
                        model_name = model_name,
                        model_type = DeviceType.rack_server,
    )
    dev.management = ipaddr
    dev.sn = sn
    dev.save()
    ipaddr.device = dev
    ipaddr.save()
    memory = _get_memory(management_url, session_id)
    for i in memory:
        index = i['index']
        mem, _ = Memory.concurrent_get_or_create(index=index, device=dev)
        mem.label = i['label']
        mem.size = i['size']
        mem.save()
        mem.model, c = ComponentModel.concurrent_get_or_create(
                name='RAM %s %dMiB' % (mem.label, mem.size), size=mem.size,
                type=ComponentType.memory.id, extra='', extra_hash='',
                family=mem.label, cores=0)
        mem.save()
    return model_name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def http_ibm_system_x(**kwargs):
    if USER is None or PASSWORD is None:
        return False, 'no credentials.', kwargs
    ip = str(kwargs['ip'])
    try:
        if not network.check_tcp_port(ip, 80):
            return False, 'closed.', kwargs
        headers, document = get_http_info(ip)
        family = guess_family(headers, document)
        if family != 'IBM System X':
            return False, 'not identified.', kwargs
        name = _run_http_ibm_system_x(ip)
        return True, name, kwargs
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs

