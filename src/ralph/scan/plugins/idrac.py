# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import uuid

import requests

from django.conf import settings
from lck.django.common.models import MACAddressField
from xml.etree import cElementTree as ET

from ralph.discovery.models import MAC_PREFIX_BLACKLIST, SERIAL_BLACKLIST
from ralph.scan.errors import Error, NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})

SCHEMA = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2"
XMLNS_S = "{http://www.w3.org/2003/05/soap-envelope}"
XMLNS_WSEN = "{http://schemas.xmlsoap.org/ws/2004/09/enumeration}"
XMLNS_WSMAN = "{http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd}"
XMLNS_N1_BASE = "{http://schemas.dell.com/wbem/wscim/1/cim-schema/2/%s}"

# Generic wsman-crafted soap message
SOAP_ENUM_WSMAN_TEMPLATE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
  <s:Header>
    <wsa:Action s:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/enumeration/Enumerate</wsa:Action>
    <wsa:To s:mustUnderstand="true">%(management_url)s</wsa:To>
    <wsman:ResourceURI s:mustUnderstand="true">%(resource)s</wsman:ResourceURI>
    <wsa:MessageID s:mustUnderstand="true">uuid:%(uuid)s</wsa:MessageID>
    <wsa:ReplyTo>
      <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
    </wsa:ReplyTo>
    <wsman:SelectorSet>
      <wsman:Selector Name="__cimnamespace">%(selector)s</wsman:Selector>
    </wsman:SelectorSet>
  </s:Header>
  <s:Body>
    <wsen:Enumerate>
      <wsman:OptimizeEnumeration/>
      <wsman:MaxElements>%(max_elements)s</wsman:MaxElements>
    </wsen:Enumerate>
  </s:Body>
</s:Envelope>
'''

FC_INFO_EXPRESSION = re.compile(r'([0-9]+)-[0-9]+')


def _send_soap(post_url, login, password, message):
    """Try to send soap message to post_url using http basic authentication.
    Note, that we don't store any session information, nor validate ssl
    certificate. Any following requests will re-send basic auth header again.
    """
    r = requests.post(
        post_url,
        data=message,
        auth=(login, password),
        verify=False,
        headers={
            'Content-Type': 'application/soap+xml;charset=UTF-8',
        },
    )
    if not r.ok:
        if r.status_code == 401:
            raise Error("Invalid username or password.")
        raise Error(
            "SoapError: Reponse was: %s\nRequest was:%s" % (r.text, message),
        )
    # soap, how I hate you...
    # sometimes errors are embedded INSIDE the envelope BUT response code is OK
    # in this case, try to detect these errors as well.
    errors_path = '{s}Body/{s}Fault'.format(s=XMLNS_S)
    errors_list = []
    errors_node = ET.XML(r.text).find(errors_path)
    if errors_node:
        errors_list = [node_text for node_text in errors_node.itertext()]
        raise Error(
            'SoapError: Request was:%s, Response errors were:%s' %
            (message, ','.join(errors_list))
        )
    # return raw xml data...
    return r.text


class IDRAC(object):

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def run_command(self, class_name, selector='root/dcim'):
        management_url = "https://%s/wsman" % self.host
        generated_uuid = uuid.uuid1()
        message = SOAP_ENUM_WSMAN_TEMPLATE % dict(
            resource=SCHEMA.rstrip('/') + '/' + class_name,
            management_url=management_url,
            uuid=generated_uuid,
            selector=selector,
            max_elements=255,
        )
        return ET.XML(_send_soap(
            'https://%s/wsman' % self.host,
            self.user,
            self.password,
            message,
        ))


def _get_base_info(idrac):
    tree = idrac.run_command('DCIM_SystemView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_SystemView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_SystemView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    records = tree.findall(q)
    if not records:
        raise Error("Incorrect answer in the _get_base_info.")
    result = {
        'model_name': "{} {}".format(
            records[0].find(
                "{}{}".format(xmlns_n1, 'Manufacturer'),
            ).text.strip().replace(" Inc.", ""),
            records[0].find(
                "{}{}".format(xmlns_n1, 'Model'),
            ).text.strip(),
        ),
    }
    serial_number = records[0].find(
        "{}{}".format(xmlns_n1, 'ChassisServiceTag'),
    ).text.strip()
    if serial_number not in SERIAL_BLACKLIST:
        result['serial_number'] = serial_number
    return result


def _get_mac_addresses(idrac_manager):
    tree = idrac_manager.run_command('DCIM_NICView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_NICView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_NICView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    mac_addresses = [
        record.find(
            "{}{}".format(xmlns_n1, 'CurrentMACAddress'),
        ).text.strip() for record in tree.findall(q)
    ]
    return [
        MACAddressField.normalize(mac)
        for mac in mac_addresses
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST
    ]


def _get_processors(idrac_manager):
    tree = idrac_manager.run_command('DCIM_CPUView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_CPUView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_CPUView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    results = []
    for record in tree.findall(q):
        model = record.find("{}{}".format(xmlns_n1, 'Model')).text.strip()
        try:
            index = int(
                record.find(
                    "{}{}".format(xmlns_n1, 'InstanceID'),
                ).text.strip().split('.')[-1],
            )
        except (ValueError, IndexError):
            continue
        results.append({
            'cores': record.find(
                "{}{}".format(xmlns_n1, 'NumberOfProcessorCores'),
            ).text.strip(),
            'model_name': model,
            'speed': record.find(
                "{}{}".format(xmlns_n1, 'MaxClockSpeed'),
            ).text.strip(),
            'index': index,
            'family': record.find(
                "{}{}".format(xmlns_n1, 'CPUFamily'),
            ).text.strip(),
            'label': model,
        })
    return results


def _get_memory(idrac_manager):
    tree = idrac_manager.run_command('DCIM_MemoryView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_MemoryView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_MemoryView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    return [
        {
            'label': '{} {}'.format(
                record.find(
                    "{}{}".format(xmlns_n1, 'Manufacturer'),
                ).text.strip(),
                record.find(
                    "{}{}".format(xmlns_n1, 'Model'),
                ).text.strip(),
            ),
            'size': record.find(
                "{}{}".format(xmlns_n1, 'Size'),
            ).text.strip(),
            'speed': record.find(
                "{}{}".format(xmlns_n1, 'Speed'),
            ).text.strip(),
            'index': index,
        } for index, record in enumerate(tree.findall(q), start=1)
    ]


def _get_disks(idrac_manager):
    tree = idrac_manager.run_command('DCIM_PhysicalDiskView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_PhysicalDiskView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_PhysicalDiskView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    results = []
    for record in tree.findall(q):
        manufacturer = record.find(
            "{}{}".format(xmlns_n1, 'Manufacturer'),
        ).text.strip()
        model_name = '{} {}'.format(
            manufacturer,
            record.find(
                "{}{}".format(xmlns_n1, 'Model')
            ).text.strip(),
        )
        results.append({
            'size': int(
                int(
                    record.find(
                        "{}{}".format(xmlns_n1, 'SizeInBytes'),
                    ).text.strip(),
                ) / 1024 / 1024 / 1024
            ),
            'serial_number': record.find(
                "{}{}".format(xmlns_n1, 'SerialNumber'),
            ).text.strip(),
            'label': model_name,
            'model_name': model_name,
            'family': manufacturer,
        })
    return results


def _get_fibrechannel_cards(idrac_manager):
    tree = idrac_manager.run_command('DCIM_PCIDeviceView')
    xmlns_n1 = XMLNS_N1_BASE % "DCIM_PCIDeviceView"
    q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_PCIDeviceView".format(
        XMLNS_S,
        XMLNS_WSEN,
        XMLNS_WSMAN,
        xmlns_n1,
    )
    used_ids = set()
    results = []
    for record in tree.findall(q):
        label = record.find(
            "{}{}".format(xmlns_n1, "Description"),
        ).text
        if 'fibre channel' not in label.lower():
            continue
        match = FC_INFO_EXPRESSION.search(
            record.find(
                "{}{}".format(xmlns_n1, "FQDD"),
            ).text,
        )
        if not match:
            continue
        physical_id = match.group(1)
        if physical_id in used_ids:
            continue
        used_ids.add(physical_id)
        results.append({
            'physical_id': physical_id,
            'label': label,
        })
    return results


def idrac_device_info(idrac_manager):
    device_info = _get_base_info(idrac_manager)
    mac_addresses = _get_mac_addresses(idrac_manager)
    if mac_addresses:
        device_info['mac_addresses'] = mac_addresses
    processors = _get_processors(idrac_manager)
    if processors:
        device_info['processors'] = processors
    memory = _get_memory(idrac_manager)
    if memory:
        device_info['memory'] = memory
    disks = _get_disks(idrac_manager)
    if disks:
        device_info['disks'] = disks
    fibrechannel_cards = _get_fibrechannel_cards(idrac_manager)
    if fibrechannel_cards:
        device_info['fibrechannel_cards'] = fibrechannel_cards
    return device_info


def scan_address(ip_address, **kwargs):
    http_family = (kwargs.get('http_family', '') or '').strip()
    if http_family and http_family.lower() not in ('dell', 'embedthis-http'):
        raise NoMatchError('It is not Dell.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('idrac', messages)
    if not user or not password:
        result.update(status='error')
        messages.append('Not configured.')
    else:
        idrac_manager = IDRAC(ip_address, user, password)
        try:
            device_info = idrac_device_info(idrac_manager)
        except Error as e:
            result.update(status='error')
            messages.append(unicode(e))
        else:
            device_info['management_ip_addresses'] = [ip_address]
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
