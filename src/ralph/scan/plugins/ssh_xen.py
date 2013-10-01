#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from django.conf import settings
from django.utils.encoding import force_unicode

from ralph.util import network, parse
from ralph.discovery import hardware
from ralph.scan.plugins import get_base_result_template
from ralph.scan.errors import NotConfiguredError, NoMatchError


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
XEN_USER, XEN_PASSWORD = SETTINGS['xen_user'], SETTINGS['xen_password']


def _connect_ssh(ip):
    return network.connect_ssh(ip, XEN_USER, XEN_PASSWORD)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line


def get_macs(ssh):
    """Get a dict of sets of macs of all the virtual machines."""

    macs = collections.defaultdict(set)
    label = ''
    for line in _ssh_lines(ssh, 'sudo xe vif-list params=vm-name-label,MAC'):
        line = force_unicode(line, errors='ignore').strip()
        if not line:
            continue
        if line.startswith('vm-name-label'):
            label = line.split(':', 1)[1].strip()
        if label.startswith('Transfer VM for'):
            continue
        if line.startswith('MAC'):
            mac = line.split(':', 1)[1].strip()
            macs[label].add(mac)
    return macs


def get_disks(ssh):
    """Get a dict of lists of disks of virtual machines."""

    stdin, stdout, stderr = ssh.exec_command(
        'sudo xe vm-disk-list '
        'vdi-params=sr-uuid,uuid,virtual-size '
        'vbd-params=vm-name-label,type,device '
        '--multiple'
    )
    disks = collections.defaultdict(list)
    vm = None
    sr_uuid = None
    device = None
    type_ = None
    device = None
    size = None
    uuid = None
    for line in stdout:
        if not line.strip():
            continue
        key, value = (x.strip() for x in line.split(':', 1))
        if key.startswith('vm-name-label '):
            vm = value
        elif key.startswith('sr-uuid '):
            sr_uuid = value
        elif key.startswith('type '):
            type_ = value
        elif key.startswith('device '):
            device = value
        elif key.startswith('uuid '):
            uuid = value
        elif key.startswith('virtual-size '):
            if type_ in {'Disk'}:
                disks[vm].append((uuid, sr_uuid, int(int(value)/1024/1024),
                                  device))
    return disks


def get_srs(ssh):
    """Get a dict of disk SRs on the hypervisor."""

    stdin, stdout, stderr = ssh.exec_command(
        'sudo xe sr-list '
        'params=uuid,physical-size,type'
    )
    srs = {}
    size = None
    uuid = None
    for line in stdout:
        if not line.strip():
            continue
        key, value = (x.strip() for x in line.split(':', 1))
        if key.startswith('uuid '):
            uuid = value
        elif key.startswith('physical-size '):
            size = int(int(value)/1024/1024)
        elif key.startswith('type '):
            if value in {'lvm'} and size > 0:
                srs[uuid] = size
    return srs


def get_running_vms(ssh):
    """Get a set of virtual machines running on the host."""

    stdin, stdout, stderr = ssh.exec_command(
        'sudo xe vm-list '
        'params=uuid,name-label,power-state,VCPUs-number,memory-actual'
    )
    data = stdout.read()
    vms = set()
    for vm_data in data.split('\n\n'):
        info = parse.pairs(lines=[
            line.replace('( RO)', '')
                .replace('( RW)', '')
                .replace('(MRO)', '').strip()
            for line in vm_data.splitlines()])
        if not info:
            continue
        label = info['name-label']
        if (
            label.startswith('Transfer VM for') or
            label.startswith('Control domain on host:')
        ):
            # Skip the helper virtual machines
            continue
        power = info['power-state']
        if power not in {'running'}:
            # Only include the running virtual machines
            continue
        cores = int(info['VCPUs-number'])
        memory = int(int(info['memory-actual'])/1024/1024)
        uuid = info['uuid']
        vms.add((label, uuid, cores, memory))
    return vms


def run_ssh_xen(ipaddr):
    ssh = _connect_ssh(ipaddr)
    try:
        vms = get_running_vms(ssh)
        macs = get_macs(ssh)
        disks = get_disks(ssh)
        shares = hardware.get_disk_shares(ssh)
    finally:
        ssh.close()
    dev = {'subdevices': []}
    for vm_name, vm_uuid, vm_cores, vm_memory in vms:
        vm_device = {}
        vm_device['mac_addresses'] = [
            mac for i, mac in enumerate(macs.get(vm_name, []))
        ]
        vm_device['serial_number'] = vm_uuid
        vm_device['hostname'] = vm_name
        vm_device['processors'] = [
            {
                'family': 'XEN Virtual',
                'name': 'XEN Virtual CPU',
                'label': 'CPU %d' % i,
                'model_name': 1,  # This would be set up in Compontent.create()
            } for i in xrange(vm_cores)
        ]
        vm_device['memory'] = [
            {
                'family': 'Virtual',
                'size': vm_memory,
                'label': 'XEN Virtual',
            },
        ]
        vm_disks = disks.get(vm_name, [])
        for uuid, sr_uuid, size, device in vm_disks:
            wwn, mount_size = shares.get('VHD-%s' % sr_uuid, (None, None))
            if wwn:
                share = {
                    'serial_number': wwn,
                    'is_virtual': True,
                    'size': mount_size,
                    'volume': device,
                }
                if not 'disk_shares' in vm_device:
                    vm_device['disk_shares'] = []
                vm_device['disk_shares'].append(share)
            else:
                storage = {}
                storage['size'] = size
                storage['label'] = device
                if not 'disks' in vm_device:
                    vm_device['disks'] = []
                vm_device['disks'].append(storage)
        dev['subdevices'].append(vm_device)
    return dev


def scan_address(ip, **kwargs):
    if XEN_USER is None:
        raise NotConfiguredError("Xen credentials not set.")
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        raise NoMatchError("Incompatible Nexus found.")
    if 'xen' not in kwargs.get('snmp_name', ''):
        raise NoMatchError("XEN not found.")
    device = run_ssh_xen(ip)
    ret = {
        'status': 'success',
        'device': device,
    }
    tpl = get_base_result_template('ssh_xen')
    tpl.update(ret)
    return tpl
