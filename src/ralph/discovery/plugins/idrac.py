#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import hashlib
import ssl
import subprocess
import time

from django.conf import settings
from lck.django.common import nested_commit_on_success
from tempfile import mkstemp
from xml.etree import cElementTree as ET

from ralph.discovery.models import (
    DeviceType, Device, Processor, IPAddress, ComponentModel, ComponentType,
    Memory, Storage
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


class Error(Exception):
    pass


class AuthError(Error):
    pass


class IncorrectQuery(Error):
    pass


class IncorrectAnswer(Error):
    pass


class IDRAC(object):
    def __init__(self, host, user=IDRAC_USER, password=IDRAC_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def _get_cert(self):
        (handle, path) = mkstemp()
        cert = ssl.get_server_certificate((self.host, 443))
        os.write(handle, cert)
        os.close(handle)
        return path

    def _check_response(self, response, command):
        tree = ET.XML(response)
        q = "{0}Body/{0}Fault".format(XMLNS_S)
        if tree.findall(q):
            command = " ".join(command)
            command = command.replace(" %s " % self.user, " ***** ")
            command = command.replace(" %s " % self.password, " ***** ")
            raise IncorrectQuery("Query: %s" % command)

    def _run_command(self, class_name, namespace='root/dcim'):
        command = [
            "wsman", "enumerate", "%s/%s" % (SCHEMA, class_name),
            "-N", namespace, "-u", self.user, "-p", self.password,
            "-h", self.host, "-P", "443", "-v", "-j", "utf-8",
            "-y", "basic", "-o", "-m", "256", "-V", "-c", self._get_cert(),
        ]
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        seconds = 0
        max_time = 10
        while proc.poll() is None:
            time.sleep(1)
            seconds += 1
            if seconds > max_time:
                proc.kill()
        out = proc.stdout.read()
        if 'authentication failed' in out.lower():
            raise AuthError("Invalid username or password.")
        self._check_response(out, command)
        return unicode(out, 'utf-8', 'replace')

    def get_base_info(self):
        soap_result = self._run_command('DCIM_SystemView')
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
            raise IncorrectAnswer("Incorrect answer in get_base_info.")
        result = {
            'manufacturer': records[0].find(
                "{}{}".format(xmlns_n1, 'Manufacturer')
            ).text,
            'model': records[0].find(
                "{}{}".format(xmlns_n1, 'Model')
            ).text,
            'sn': records[0].find(
                "{}{}".format(xmlns_n1, 'ChassisServiceTag')
            ).text

        }
        return result

    def get_ethernets(self):
        soap_result = self._run_command('DCIM_NICView')
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
                ).text,

            })
        return results

    def get_cpu(self):
        soap_result = self._run_command('DCIM_CPUView')
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
        soap_result = self._run_command('DCIM_MemoryView')
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
        soap_result = self._run_command('DCIM_PhysicalDiskView')
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
            })
        return results


def _save_ethernets(data):
    ethernets = [Eth(label=eth['label'], mac=eth['mac'], speed=0)
                 for eth in data]
    return ethernets


def _save_cpu(dev, data):
    for cpu in data:
        try:
            index = int(cpu['socket'].split('.')[-1])
        except (ValueError, IndexError):
            continue
        extra = "{} family: {} speed: {} cores: {}".format(
            cpu['model'],
            cpu['family'],
            cpu['speed'],
            cpu['cores_count']
        )
        model, _ = ComponentModel.concurrent_get_or_create(
            speed=cpu['speed'],
            type=ComponentType.processor,
            family=cpu['family'],
            cores=cpu['cores_count'],
            extra_hash=hashlib.md5(extra).hexdigest()
        )
        model.name = cpu['model']
        model.save(priority=SAVE_PRIORITY)
        processor, _ = Processor.concurrent_get_or_create(
            device=dev,
            index=index
        )
        processor.label = cpu['model']
        processor.model = model
        processor.speed = cpu['speed']
        processor.cores = cpu['cores_count']
        processor.save(priority=SAVE_PRIORITY)


def _save_memory(dev, data):
    for mem, index in zip(data, range(1, len(data) + 1)):
        extra = "RAM {} {} {}MiB speed: {}".format(
            mem['manufacturer'],
            mem['model'],
            mem['size'],
            mem['speed']
        )
        name = "{} {}".format(mem['manufacturer'], mem['model'])

        model, _ = ComponentModel.concurrent_get_or_create(
            speed=mem['speed'],
            type=ComponentType.memory,
            extra_hash=hashlib.md5(extra).hexdigest()
        )
        model.name = name
        model.save(priority=SAVE_PRIORITY)
        memory, _ = Memory.concurrent_get_or_create(index=index, device=dev)
        memory.label = name
        memory.size = mem['size']
        memory.speed = mem['speed']
        memory.model = model
        memory.save(priority=SAVE_PRIORITY)


def _save_storage(dev, data):
    for disk in data:
        model_name = "{} {}".format(
            disk['manufacturer'].strip(),
            disk['model'].strip()
        )
        size = int(int(disk['size']) / 1024 / 1024 / 1024)
        model, _ = ComponentModel.concurrent_get_or_create(
            size=size, type=ComponentType.disk, speed=0, cores=0,
            extra='', extra_hash=hashlib.md5('').hexdigest(),
            family=model_name
        )
        model.name = model_name
        model.save(priority=SAVE_PRIORITY)
        storage, _ = Storage.concurrent_get_or_create(
            device=dev, sn=disk['sn']
        )
        storage.model = model
        storage.label = "{} {}MiB".format(model_name, size)
        storage.size = size
        storage.save(priority=SAVE_PRIORITY)


@nested_commit_on_success
def _run_idrac(ip):
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
    return model_name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def idrac(**kwargs):
    if not IDRAC_USER or not IDRAC_PASSWORD:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    http_family = kwargs.get('http_family')
    if http_family not in ('Mbedthis-Appweb', ):
        return False, 'no match', kwargs
    name = _run_idrac(ip)
    return True, name, kwargs

