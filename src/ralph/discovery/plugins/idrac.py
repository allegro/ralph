#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import uuid

from django.conf import settings
from lck.django.common import nested_commit_on_success
import requests
from xml.etree import cElementTree as ET

from ralph.discovery.models import (
    DeviceType, Device, Processor, IPAddress, ComponentModel, ComponentType,
    Memory, Storage, FibreChannel
)
from ralph.util import plugin, Eth

SAVE_PRIORITY = 52
IDRAC_USER = settings.IDRAC_USER
IDRAC_PASSWORD = settings.IDRAC_PASSWORD

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


class Error(Exception):
    pass


class AuthError(Error):
    pass


class IncorrectAnswerError(Error):
    pass


class SoapError(Error):
    pass


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
            'Content-Type': 'application/soap+xml;charset=UTF-8'
        }
    )
    if not r.ok:
        if r.status_code == 401:
            raise AuthError("Invalid username or password.")
        raise SoapError(
            "Reponse was: %s\nRequest was:%s" % (r.text, message)
        )
    # soap, how I hate you...
    # sometimes errors are embedded INSIDE the envelope BUT response code is OK
    # in this case, try to detect these errors as well.
    errors_path = '{s}Body/{s}Fault'.format(s=XMLNS_S)
    errors_list = []
    errors_node = ET.XML(r.text).find(errors_path)
    if errors_node:
        errors_list = [node_text for node_text in errors_node.itertext()]
        raise SoapError(
            'Request was:%s, Response errors were:%s' %
            (message, ','.join(errors_list))
        )
    # return raw xml data...
    return r.text


class IDRAC(object):

    def __init__(self, host, user=IDRAC_USER, password=IDRAC_PASSWORD):
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
        return _send_soap(
            'https://%s/wsman' % self.host,
            self.user, self.password, message
        )

    def get_base_info(self):
        soap_result = self.run_command('DCIM_SystemView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_SystemView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_SystemView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        records = tree.findall(q)
        if not records:
            raise IncorrectAnswerError(
                "Incorrect answer in the get_base_info.")
        result = {
            'manufacturer': records[0].find(
                "{}{}".format(xmlns_n1, 'Manufacturer')
            ).text.strip(),
            'model': records[0].find(
                "{}{}".format(xmlns_n1, 'Model')
            ).text.strip(),
            'sn': records[0].find(
                "{}{}".format(xmlns_n1, 'ChassisServiceTag')
            ).text

        }
        return result

    def get_ethernets(self):
        soap_result = self.run_command('DCIM_NICView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_NICView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_NICView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        results = []
        for record in tree.findall(q):
            results.append({
                'mac': record.find(
                    "{}{}".format(xmlns_n1, 'CurrentMACAddress')
                ).text,
                'label': record.find(
                    "{}{}".format(xmlns_n1, 'ProductName')
                ).text
            })
        return results

    def get_cpu(self):
        soap_result = self.run_command('DCIM_CPUView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_CPUView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_CPUView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        results = []
        for record in tree.findall(q):
            results.append({
                'cores_count': record.find(
                    "{}{}".format(xmlns_n1, 'NumberOfProcessorCores')
                ).text,
                'model': record.find(
                    "{}{}".format(xmlns_n1, 'Model')
                ).text,
                'speed': record.find(
                    "{}{}".format(xmlns_n1, 'MaxClockSpeed')
                ).text,
                'manufacturer': record.find(
                    "{}{}".format(xmlns_n1, 'Manufacturer')
                ).text,
                'socket': record.find(
                    "{}{}".format(xmlns_n1, 'InstanceID')
                ).text,
                'family': record.find(
                    "{}{}".format(xmlns_n1, 'CPUFamily')
                ).text
            })
        return results

    def get_memory(self):
        soap_result = self.run_command('DCIM_MemoryView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_MemoryView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_MemoryView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        results = []
        for record in tree.findall(q):
            results.append({
                'size': record.find(
                    "{}{}".format(xmlns_n1, 'Size')
                ).text,
                'speed': record.find(
                    "{}{}".format(xmlns_n1, 'Speed')
                ).text,
                'sn': record.find(
                    "{}{}".format(xmlns_n1, 'SerialNumber')
                ).text,
                'model': record.find(
                    "{}{}".format(xmlns_n1, 'Model')
                ).text,
                'manufacturer': record.find(
                    "{}{}".format(xmlns_n1, 'Manufacturer')
                ).text,
                'socket': record.find(
                    "{}{}".format(xmlns_n1, 'InstanceID')
                ).text
            })
        return results

    def get_storage(self):
        soap_result = self.run_command('DCIM_PhysicalDiskView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_PhysicalDiskView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_PhysicalDiskView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        results = []
        for record in tree.findall(q):
            results.append({
                'size': record.find(
                    "{}{}".format(xmlns_n1, 'SizeInBytes')
                ).text.strip(),
                'sn': record.find(
                    "{}{}".format(xmlns_n1, 'SerialNumber')
                ).text.strip(),
                'model': record.find(
                    "{}{}".format(xmlns_n1, 'Model')
                ).text.strip(),
                'manufacturer': record.find(
                    "{}{}".format(xmlns_n1, 'Manufacturer')
                ).text.strip(),
            })
        return results

    def get_fc_cards(self):
        soap_result = self.run_command('DCIM_PCIDeviceView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_PCIDeviceView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_PCIDeviceView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        used_ids = []
        results = []
        for record in tree.findall(q):
            label = record.find(
                "{}{}".format(xmlns_n1, "Description")
            ).text
            if 'fibre channel' not in label.lower():
                continue
            match = re.search(
                r'([0-9]+)-[0-9]+',
                record.find(
                    "{}{}".format(xmlns_n1, "FQDD")
                ).text
            )
            if not match:
                continue
            physical_id = match.group(1)
            if physical_id in used_ids:
                continue
            used_ids.append(physical_id)
            results.append({
                'physical_id': physical_id,
                'label': label
            })
        return results


def _save_ethernets(data):
    ethernets = [Eth(label=eth['label'], mac=eth['mac'], speed=0)
                 for eth in data]
    return ethernets


def _save_cpu(dev, data):
    detected_cpus = []
    for cpu in data:
        try:
            index = int(cpu['socket'].split('.')[-1])
        except (ValueError, IndexError):
            continue
        model, _ = ComponentModel.create(
            ComponentType.processor,
            speed=cpu['speed'],
            family=cpu['family'],
            cores=cpu['cores_count'],
            name=cpu['model'],
            priority=SAVE_PRIORITY,
        )
        processor, _ = Processor.concurrent_get_or_create(
            device=dev,
            index=index
        )
        processor.label = cpu['model']
        processor.model = model
        processor.speed = cpu['speed']
        processor.cores = cpu['cores_count']
        processor.save(priority=SAVE_PRIORITY)
        detected_cpus.append(processor.pk)
    dev.processor_set.exclude(pk__in=detected_cpus).delete()


def _save_memory(dev, data):
    detected_memory = []
    for mem, index in zip(data, range(1, len(data) + 1)):
        model, _ = ComponentModel.create(
            ComponentType.memory,
            size=int(mem['size']),
            speed=int(mem['speed']),
            priority=SAVE_PRIORITY,
        )
        memory, _ = Memory.concurrent_get_or_create(index=index, device=dev)
        memory.label = "{} {}".format(mem['manufacturer'], mem['model'])
        memory.size = mem['size']
        memory.speed = mem['speed']
        memory.model = model
        memory.save(priority=SAVE_PRIORITY)
        detected_memory.append(memory.pk)
    dev.memory_set.exclude(pk__in=detected_memory).delete()


def _save_storage(dev, data):
    detected_storage = []
    for disk in data:
        model_name = "{} {}".format(
            disk['manufacturer'],
            disk['model']
        )
        size = int(int(disk['size']) / 1024 / 1024 / 1024)
        model, _ = ComponentModel.create(
            ComponentType.disk,
            size=size,
            family=model_name,
            priority=SAVE_PRIORITY,
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=dev,
            sn=disk['sn'],
            mount_point=None,
        )
        storage.model = model
        storage.label = model.name
        storage.size = size
        storage.save(priority=SAVE_PRIORITY)
        detected_storage.append(storage.pk)
    dev.storage_set.exclude(pk__in=detected_storage).delete()


def _save_fc_cards(dev, data):
    detected_fc_cards = []
    for card in data:
        model, _ = ComponentModel.create(
            ComponentType.fibre,
            family=card['label'],
            name=card['label'],
            priority=SAVE_PRIORITY,
        )
        fc, _ = FibreChannel.concurrent_get_or_create(
            device=dev, physical_id=card['physical_id']
        )
        fc.model = model
        fc.label = card['label']
        fc.save(priority=SAVE_PRIORITY)
        detected_fc_cards.append(fc.pk)
    dev.fibrechannel_set.exclude(pk__in=detected_fc_cards).delete()


@nested_commit_on_success
def run_idrac(ip):
    idrac = IDRAC(ip)
    base_info = idrac.get_base_info()
    model_name = "{} {}".format(
        base_info['manufacturer'].replace(" Inc.", ""),
        base_info['model']
    )
    ethernets = _save_ethernets(idrac.get_ethernets())
    ip_address, _ = IPAddress.concurrent_get_or_create(address=ip)
    ip_address.is_management = True
    ip_address.save()
    dev = Device.create(
        ethernets=ethernets,
        model_name=model_name,
        sn=base_info['sn'],
        model_type=DeviceType.rack_server,
    )
    dev.management = ip_address
    dev.save(priority=SAVE_PRIORITY)
    ip_address.device = dev
    ip_address.save()
    _save_cpu(dev, idrac.get_cpu())
    _save_memory(dev, idrac.get_memory())
    _save_storage(dev, idrac.get_storage())
    _save_fc_cards(dev, idrac.get_fc_cards())
    return model_name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def idrac(**kwargs):
    if not IDRAC_USER or not IDRAC_PASSWORD:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    http_family = kwargs.get('http_family')
    if http_family.lower() not in ('dell', 'embedthis-http'):
        return False, 'no match', kwargs
    name = run_idrac(ip)
    return True, name, kwargs
