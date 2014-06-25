#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings

from ralph.util import network
from ralph.discovery import guessmodel
from ralph.scan.errors import NotConfiguredError, NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
AIX_USER = SETTINGS['aix_user']
AIX_PASSWORD = SETTINGS['aix_password']
AIX_KEY = SETTINGS['aix_key']

MODELS = {
    'IBM,9131-52A': 'IBM P5 520',
    'IBM,8203-E4A': 'IBM P6 520',
    'IBM,8233-E8B': 'IBM Power 750 Express',
}


def normalize_wwn(wwn):
    if wwn[-4:] == "5000" and wwn[:4] != "5000":
        return "5000{}".format(wwn[:-4])
    return wwn


def _connect_ssh(ip):
    return network.connect_ssh(ip, AIX_USER, AIX_PASSWORD, key=AIX_KEY)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line


def run_ssh_aix(ip):
    device = {}
    ssh = _connect_ssh(ip)
    try:
        device['mac_addresses'] = []
        for model_line in _ssh_lines(ssh, 'lsattr -El sys0 | grep ^modelname'):
            machine_model = model_line.split(None, 2)[1]
            break
        for mac_line in _ssh_lines(ssh, 'netstat -ia | grep link'):
            interface, mtu, net, mac, rest = mac_line.split(None, 4)
            if '.' not in mac:
                continue
            octets = mac.split('.')
            mac = ''.join('%02x' % int(o, 16) for o in octets).upper()
            device['mac_addresses'].append(mac)
        disks = {}
        os_storage_size = 0
        for disk_line in _ssh_lines(ssh, 'lsdev -c disk'):
            disk, rest = disk_line.split(None, 1)
            model = None
            for line in _ssh_lines(ssh, 'lscfg -vl %s' % disk):
                if 'hdisk' in line:
                    match = re.search(r'\(([0-9]+) MB\)', line)
                    if match:
                        os_storage_size += int(match.group(1))
                elif 'Serial Number...' in line:
                    label, sn = line.split('.', 1)
                    sn = sn.strip('. \n')
                elif 'Machine Type and Model.' in line:
                    label, model = line.split('.', 1)
                    model = model.strip('. \n')
            disks[disk] = (model, sn)
        os_version = ''
        for line in _ssh_lines(ssh, 'oslevel'):
            os_version = line.strip()
            break
        os_memory = 0
        for line in _ssh_lines(ssh, 'lsattr -El sys0 | grep ^realmem'):
            match = re.search(r'[0-9]+', line)
            if match:
                os_memory = int(int(match.group(0)) / 1024)
            break
        os_corescount = 0
        for line in _ssh_lines(ssh, 'lparstat -i|grep ^Active\ Phys'):
            match = re.search(r'[0-9]+', line)
            if match:
                os_corescount += int(match.group(0))
    finally:
        ssh.close()
    device['model_name'] = '%s AIX' % MODELS.get(machine_model, machine_model)
    device['system_ip_addresses'] = [ip]
    wwns = []
    sns = []
    stors = []
    for disk, (model_name, sn) in disks.iteritems():
        if not sn:
            continue
        if model_name == 'VV':
            wwns.append(sn)
        else:
            stors.append((disk, model_name, sn))
            sns.append(sn)
    device['disk_shares'] = [
        {'serial_number': normalize_wwn(wwn)} for wwn in wwns
    ]
    for disk, model_name, sn in stors:
        if 'disks' not in device:
            device['disks'] = []
        device['disks'].append({
            'serial_number': sn,
            'label': disk,
            'model_name': model_name
        })
    device['system_label'] = 'AIX ver. %s' % os_version
    if os_memory:
        device['system_memory'] = os_memory
    if os_storage_size:
        device['system_storage'] = os_storage_size
    if os_corescount:
        device['system_cores_count'] = os_corescount
    device['system_family'] = 'AIX'
    return device


def scan_address(ip, **kwargs):
    snmp_name = kwargs.get('snmp_name', '') or ''
    if 'nx-os' in snmp_name.lower():
        raise NoMatchError("Incompatible Nexus found.")
    if snmp_name and not snmp_name.startswith('IBM PowerPC'):
        raise NoMatchError("No match")
    if AIX_USER is None:
        raise NotConfiguredError("No credentials set up.")
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gvendor != 'IBM':
        raise NoMatchError("No match")
    device = run_ssh_aix(ip)
    ret = {
        'status': 'success',
        'device': device,
    }
    tpl = get_base_result_template('ssh_cisco_catalyst')
    tpl.update(ret)
    return tpl
