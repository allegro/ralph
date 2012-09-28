#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import subprocess

from lck.lang import nullify
from django.conf import settings
from lck.django.common import nested_commit_on_success
from lck.django.common.models import MACAddressField

from ralph.util import network, parse
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, EthernetSpeed, Device,
        Processor, Memory, Ethernet, IPAddress, ComponentModel,
        ComponentType, SERIAL_BLACKLIST)


IPMI_SECTION_REGEX = re.compile(r'FRU Device Description : (?P<value>[^(]+) '
    r'\(ID (?P<id>\d+)\)')
IPMI_OPTION_REGEX = re.compile(r' (?P<key>[^:]+) : (?P<value>.*)')
IPMI_USER = settings.IPMI_USER
IPMI_PASSWORD = settings.IPMI_PASSWORD

SAVE_PRIORITY = 55

class Error(Exception):
    pass

class IPMIToolError(Error):
    pass

class AnswerError(Error):
    pass

class AuthError(IPMIToolError):
    pass

def _clean(raw):
    if raw:
        stripped = raw
        for strip in " .:-_0":
            stripped = stripped.replace(strip, '')
        if stripped:
            return raw, True
    return raw, False


class IPMI(object):
    def __init__(self, host, user=IPMI_USER, password=IPMI_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def tool(self, command, subcommand, param=None):
        command = ["ipmitool", "-H", self.host, "-U", self.user,
                   "-P", self.password, command, subcommand]
        if param:
            command.append(param)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode and err:
            if err.startswith('Invalid user name'):
                raise AuthError('Invalid user name')
            else:
                raise IPMIToolError('Error calling ipmitool: %s' % err)
        return unicode(out, 'utf-8', 'replace')


    def get_fru(self):
        out = self.tool('fru', 'print')
        ipmi = parse.pairs(out)
        # remove (ID XX) from the top-level keys
        ipmi = dict((re.sub(r'\s*[(][^)]*[)]', '', k), v)
                    for (k, v) in ipmi.iteritems())
        return nullify(ipmi)

    def get_lan(self):
        out = self.tool('lan', 'print')
        return parse.pairs(out)

    def get_mc(self):
        out = self.tool('mc', 'info')
        return parse.pairs(out)

    def get_mac(self):
        data = self.get_lan()
        mac = data.get('MAC Address')
        return mac


def _add_ipmi_lan(device, mac):
    eth, created = Ethernet.concurrent_get_or_create(device=device,
        mac=MACAddressField.normalize(mac))
    eth.label = 'IPMI MC'
    eth.save(priority=SAVE_PRIORITY)

def _get_ipmi_ethernets(data):
    # Ethernet
    index = 0
    while True:
        ethernet = data['MB/NET{}'.format(index)]
        if not ethernet:
            return
        mac = ethernet['Product Serial']
        label = " ".join((ethernet['Product Manufacturer'],
            ethernet['Product Name'])).title()
        if 'GIGABIT' in ethernet['Product Name']:
            speed = EthernetSpeed.s1gbit.id
        else:
            speed = 0
        yield Eth(label=label, mac=mac, speed=speed)
        index += 1

def _add_ipmi_components(device, data):
    # CPUs
    cpu_index = 0
    total_mem_index = 0
    while True:
        cpu = data['MB/P{}'.format(cpu_index)]
        if not cpu:
            break
        if not cpu['Product Name']:
            cpu_index += 1
            continue
        proc, _ = Processor.concurrent_get_or_create(index=cpu_index+1,
            device=device)
        proc.label = re.sub(' +', ' ', cpu['Product Name']).title()
        speed_match = re.search(r'(\d+\.\d+)GHZ', cpu['Product Name'])
        if speed_match:
            speed = int(float(speed_match.group(1)) * 1000)
        else:
            speed = 0
        cores = 0
        proc.model, c = ComponentModel.concurrent_get_or_create(
            family=proc.label, speed=speed, type=ComponentType.processor.id,
            cores=cores, extra_hash='', size=0)
        if c:
            proc.model.name = ('CPU %s %dMHz %d-core' %
                                (proc.label, speed, cores))[:50]
            proc.model.save()
        proc.save()
        # Memory
        mem_index = 0
        while True:
            memory = data['MB/P{}/D{}'.format(cpu_index, mem_index)]
            if not memory:
                break
            if not memory['Product Name']:
                mem_index += 1
                total_mem_index += 1
                continue
            size_match = re.search(r'(\d+)GB', memory['Product Name'])
            if not size_match:
                mem_index += 1
                total_mem_index += 1
                continue
            mem, _ = Memory.concurrent_get_or_create(index=total_mem_index+1,
                device=device)
            mem.label = memory['Product Name']
            size = int(size_match.group(1)) * 1024
            speed = 0
            mem.model, c = ComponentModel.concurrent_get_or_create(
                name='RAM %s %dMiB' % (mem.label, size), size=size, speed=speed,
                type=ComponentType.memory.id, extra='', extra_hash='',
                family=mem.label, cores=0)
            mem.save()
            mem_index += 1
            total_mem_index += 1
        cpu_index += 1

@nested_commit_on_success
def _run_ipmi(ip):
    try:
        ipmi = IPMI(ip)
        fru = ipmi.get_fru()
    except AuthError:
        try:
            ipmi = IPMI(ip, 'ADMIN')
            fru = ipmi.get_fru()
        except AuthError:
            ipmi = IPMI(ip, 'ADMIN', 'ADMIN')
            fru = ipmi.get_fru()
    mc = ipmi.get_mc()
    top = fru['/SYS']
    if not top:
        top = fru['Builtin FRU Device']
    if not top:
        raise AnswerError('Incompatible answer.')
    name, name_clean = _clean(top['Product Name'])
    sn, sn_clean = _clean(top['Product Serial'])
    if sn in SERIAL_BLACKLIST:
        sn = None
    model_type = DeviceType.rack_server
    if name.lower().startswith('ipmi'):
        model_type = DeviceType.unknown
    mac = ipmi.get_mac()
    if mac:
        ethernets = [Eth(label='IPMI MAC', mac=mac, speed=0)]
    else:
        ethernets = []
    ethernets.extend(_get_ipmi_ethernets(fru))
    dev = Device.create(ethernets=ethernets, priority=SAVE_PRIORITY,
                        sn=sn, model_name=name.title(), model_type=model_type)
    firmware = mc.get('Firmware Revision')
    if firmware:
        dev.mgmt_firmware = 'rev %s' % firmware
    _add_ipmi_lan(dev, mac)
    _add_ipmi_components(dev, fru)
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)

    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device = dev
    ip_address.is_management = True
    if created:
        ip_address.hostname = network.hostname(ip_address.address)
        ip_address.snmp_name = name
    ip_address.save(update_last_seen=True) # no priorities for IP addresses
    return name

@plugin.register(chain='discovery', requires=['ping', 'http'])
def ipmi(**kwargs):
    ip = str(kwargs['ip'])
    http_family = kwargs.get('http_family')
    if http_family not in ('Sun', 'Thomas-Krenn', 'Oracle-ILOM-Web-Server', 'IBM System X'):
        return False, 'no match.', kwargs
    try:
        name = _run_ipmi(ip)
    except (AnswerError, IPMIToolError) as e:
        return False, str(e), kwargs

    return True, name, kwargs

def ipmi_power_on(host, user=IPMI_USER, password=IPMI_PASSWORD):
    ipmi = IPMI(host, user, password)
    response = ipmi.tool('chassis', 'power', 'on')
    return response.strip().lower().endswith('on')

def ipmi_reboot(host, user=IPMI_USER, password=IPMI_PASSWORD,
                power_on_if_disabled=False):
    ipmi = IPMI(host, user, password)

    response = ipmi.tool('chassis', 'power', 'status')
    if response.strip().lower().endswith('on'):
        response = ipmi.tool('chassis', 'power', 'reset')
        if response.strip().lower().endswith('reset'):
            return True
    elif power_on_if_disabled:
        return ipmi_power_on(host, user, password)
    return False
