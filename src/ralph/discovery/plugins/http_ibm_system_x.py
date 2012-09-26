#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common import nested_commit_on_success
import urllib2

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, DeviceModel, Device, IPAddress,
                                    DiskShare, ComponentModel, ComponentType, Memory)

from xml.etree import cElementTree as ET

USER = settings.IBM_SYSTEM_X_USER
PASSWORD = settings.IBM_SYSTEM_X_PASSWORD


class Error(Exception):
    pass


def _send_soap(post_url, session_id, message):
    opener = urllib2.build_opener()
    request = urllib2.Request(post_url, message,
          headers={'session_id': session_id}
    )
    response = opener.open(request, timeout=5)
    if response.code != 200:
        raise Error()
    response_data = response.read()
    return response_data


def _get_session_id(ip):
    login_url = "http://%s/session/create" % ip
    login_data = "%s,%s" % (USER, PASSWORD)
    opener = urllib2.build_opener()
    request = urllib2.Request(login_url, login_data)
    response = opener.open(request, timeout=5)
    if response.code != 200:
        raise Error()
    response_data = response.readlines()
    if response_data and response_data[0][:2] =='ok':
        return response_data[0][3:]
    raise Error()

def _get_model_name(management_url, session_id):
    template = '''
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
  <SOAP-ENV:Header>
    <wsa:To>%(management_url)s</wsa:To>
    <wsa:ReplyTo>
      <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
    </wsa:ReplyTo>
    <wsman:ResourceURI>http://www.ibm.com/iBMC/sp/Monitors</wsman:ResourceURI>
    <wsa:Action>http://www.ibm.com/iBMC/sp/Monitors/GetVitalProductData</wsa:Action>
    <wsa:MessageID>dt:1348663890605</wsa:MessageID>
  </SOAP-ENV:Header>
  <SOAP-ENV:Body>
    <GetVitalProductData xmlns="http://www.ibm.com/iBMC/sp/Monitors" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetVitalProductData>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
    '''
    message = template % dict(
            management_url = management_url
    )
    soap_result = _send_soap(management_url, session_id, message)
    tree = ET.XML(soap_result)
    product_name = tree.findall('{0}Body/GetVitalProductDataResponse/GetVitalProductDataResponse/MachineLevelVPD/ProductName'.format('{http://www.w3.org/2003/05/soap-envelope}'))
    return product_name[0].text


def _get_sn(management_url, session_id):
    template_get_info = '''<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
      <SOAP-ENV:Header>
        <wsa:To>http://10.235.64.214/wsman</wsa:To>
        <wsa:ReplyTo>
          <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsman:ResourceURI>http://www.ibm.com/iBMC/sp/iBMCControl</wsman:ResourceURI>
        <wsa:Action>http://www.ibm.com/iBMC/sp/iBMCControl/GetSPNameSettings</wsa:Action>
        <wsa:MessageID>dt:1348663343290</wsa:MessageID>
      </SOAP-ENV:Header>
      <SOAP-ENV:Body>
        <GetSPNameSettings xmlns="http://www.ibm.com/iBMC/sp/iBMCControl" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetSPNameSettings>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>'''
    message_get_info = template_get_info % dict(
            management_url = management_url
    )
    soap_result = _send_soap(management_url, session_id, message_get_info)
    tree = ET.XML(soap_result)
    sn = tree.findall('{0}Body/GetSPNameSettingsResponse/SPName'.format('{http://www.w3.org/2003/05/soap-envelope}'))
    sn = sn[0].text
    return sn

def _get_memory(management_url, session_id):
    template_get_memory = '''
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
      <SOAP-ENV:Header>
        <wsa:To>%(management_url)s</wsa:To>
        <wsa:ReplyTo>
          <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsman:ResourceURI>http://www.ibm.com/iBMC/sp/Monitors</wsman:ResourceURI>
        <wsa:Action>http://www.ibm.com/iBMC/sp/Monitors/GetMemoryInfo</wsa:Action>
        <wsa:MessageID>dt:1348660868501</wsa:MessageID>
      </SOAP-ENV:Header>
      <SOAP-ENV:Body>
        <GetMemoryInfo xmlns="http://www.ibm.com/iBMC/sp/Monitors" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetMemoryInfo>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    '''
    message_get_memory = template_get_memory % dict(
            management_url = management_url
    )
    soap_result = _send_soap(management_url, session_id, message_get_memory)
    tree = ET.XML(soap_result)
    mems = []
    memory = tree.findall('{0}Body/GetMemoryInfoResponse/Memory/*'.format('{http://www.w3.org/2003/05/soap-envelope}'))
    for record in memory:
        mems.append(dict(
            label=record.find('Description').text,
            index=int(record.find('Description').text.split()[1]),
            size=int(record.find('Size').text)*1024,
        ))
    return mems


def _get_mac_addresses(management_url, session_id):
    template_get_macs = '''<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
  <SOAP-ENV:Header>
    <wsa:To>http://%(management_url)s</wsa:To>
    <wsa:ReplyTo>
      <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
    </wsa:ReplyTo>
    <wsman:ResourceURI>http://www.ibm.com/iBMC/sp/Monitors</wsman:ResourceURI>
    <wsa:Action>http://www.ibm.com/iBMC/sp/Monitors/GetHostMacAddresses</wsa:Action>
    <wsa:MessageID>dt:1348650519402</wsa:MessageID>
  </SOAP-ENV:Header>
  <SOAP-ENV:Body>
    <GetHostMacAddresses xmlns="http://www.ibm.com/iBMC/sp/Monitors" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"></GetHostMacAddresses>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
    message_get_macs = template_get_macs % dict(
            management_url = management_url
    )
    soap_result = _send_soap(management_url, session_id, message_get_macs)
    tree=ET.XML(soap_result)
    mac_addresses = tree.findall('{0}Body/GetHostMacAddressesResponse/**'.format('{http://www.w3.org/2003/05/soap-envelope}'))
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
    import pdb; pdb.set_trace()
    for i in memory:
        index = i['index']
        mem, _ = Memory.concurrent_get_or_create(index=index, device=dev)
        mem.label = i['label']
        mem.size = i['size']
        mem.save()
        #mem.model, c = ComponentModel.concurrent_get_or_create(
        #        name='RAM %s %dMiB' % (mem.label, size), size=size, speed=speed,
        #        type=ComponentType.memory.id, extra='', extra_hash='',
        #        family=mem.label, cores=0)
    return model_name

@plugin.register(chain='discovery', requires=['ping', 'http'])
def http_ibm_system_x(**kwargs):
    if USER is None or PASSWORD is None:
        return False, 'no credentials.', kwargs
    ip = str(kwargs['ip'])
    if not network.check_tcp_port(ip, 80):
        return False, 'closed.', kwargs
    try:
        name = _run_http_ibm_system_x(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs

