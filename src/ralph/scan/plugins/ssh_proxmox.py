# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os

import json

from django.conf import settings

from ralph.discovery.hardware import get_disk_shares
from ralph.discovery.models import DeviceType
from ralph.scan.errors import ConnectionError, NoMatchError, NoLanError
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


logger = logging.getLogger("SCAN")


def _connect_ssh(ip_address, user, password):
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a Proxmox server.')
    return network.connect_ssh(ip_address, user, password)


def _get_master_ip_address(ssh, ip_address, cluster_cfg=None):
    if not cluster_cfg:
        stdin, stdout, stderr = ssh.exec_command("cat /etc/pve/cluster.cfg")
        data = stdout.read()
    else:
        data = cluster_cfg
    if not data:
        stdin, stdout, stderr = ssh.exec_command("pvesh get /nodes")
        data = stdout.read()
        if data:
            for node in json.loads(data):
                stdin, stdout, stderr = ssh.exec_command(
                    'pvesh get "/nodes/%s/dns"' % node['node'],
                )
                ip_address = json.loads(stdout.read())['dns1']
                break
        else:
            return ip_address
    nodes = {}
    current_node = None
    for line in data.splitlines():
        line = line.strip()
        if line.endswith('{'):
            current_node = line.replace('{', '').strip()
            nodes[current_node] = {}
        elif line.endswith('}'):
            current_node = None
        elif ':' in line and current_node:
            key, value = (v.strip() for v in line.split(':', 1))
            nodes[current_node][key] = value
    for node, pairs in nodes.iteritems():
        is_master = node.startswith('master')
        try:
            ip_address = pairs['IP']
        except KeyError:
            continue
        if is_master:
            return ip_address


def _get_cluster_member(ssh, ip_address):
    stdin, stdout, stderr = ssh.exec_command("ifconfig eth0 | head -n 1")
    mac = stdout.readline().split()[-1]
    return {
        'model_name': 'Proxmox',
        'mac_addresses': [mac],
        'installed_software': [{
            'model_name': 'Proxmox',
            'path': 'proxmox',
        }],
        'system_ip_addresses': [ip_address],
    }


def _get_local_disk_size(ssh, disk):
    """Return the size of a disk image file, in bytes"""

    path = os.path.join('/var/lib/vz/images', disk)
    stdin, stdout, stderr = ssh.exec_command("du -m '%s'" % path)
    line = stdout.read().strip()
    if not line:
        return 0
    size = int(line.split(None, 1)[0])
    return size


def _get_virtual_machine_info(
    ssh,
    vmid,
    master_ip_address,
    storages,
    hypervisor_ip_address,
):
    stdin, stdout, stderr = ssh.exec_command(
        "cat /etc/qemu-server/%d.conf" % vmid,
    )
    lines = stdout.readlines()
    if not lines:
        # Proxmox 2 uses a different directory structure
        stdin, stdout, stderr = ssh.exec_command(
            "cat /etc/pve/nodes/*/qemu-server/%d.conf" % vmid,
        )
        lines = stdout.readlines()
    disks = {}
    lan_model = None
    name = 'unknown'
    for line in lines:
        line = line.strip()
        if line.startswith('#') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        if key.startswith('vlan'):
            lan_model, lan_mac = value.split('=', 1)
        elif key.startswith('net'):
            lan_model, lan_mac = value.split('=', 1)
            if ',' in lan_mac:
                lan_mac = lan_mac.split(',', 1)[0]
        elif key == 'name':
            name = value.strip()
        elif key == 'sockets':
            cpu_count = int(value.strip())
        elif key.startswith('ide') or key.startswith('virtio'):
            disks[key] = value.strip()
    if lan_model is None:
        raise NoLanError(
            "No LAN for virtual server %s. Hypervisor IP: %s" % (
                vmid,
                hypervisor_ip_address,
            ),
        )
    device_info = {
        'model_name': 'Proxmox qemu kvm',
        'type': DeviceType.virtual_server.raw,
        'mac_addresses': [lan_mac],
        'management': master_ip_address,  # ?
        'hostname': name,
    }
    detected_disks = []
    detected_shares = []
    for slot, disk in disks.iteritems():
        params = {}
        if ',' in disk:
            disk, rawparams = disk.split(',', 1)
            for kv in rawparams.split(','):
                if not kv.strip():
                    continue
                k, v = kv.split('=', 1)
                params[k] = v.strip()
        if ':' in disk:
            vg, lv = disk.split(':', 1)
        else:
            vg = ''
            lv = disk
        if vg == 'local':
            size = _get_local_disk_size(ssh, lv)
            if not size > 0:
                continue
            detected_disks.append({
                'family': 'QEMU disk image',
                'size': size,
                'label': slot,
                'mount_point': lv,
            })
            continue
        if vg in ('', 'local', 'pve-local'):
            continue
        vol = '%s:%s' % (vg, lv)
        try:
            wwn, size = storages[lv]
        except KeyError:
            logger.warning(
                'Volume %s does not exist. Hypervisor IP: %s' % (
                    lv,
                    hypervisor_ip_address,
                ),
            )
            continue
        detected_shares.append({
            'serial_number': wwn,
            'is_virtual': True,
            'size': size,
            'volume': vol,
        })
    if detected_disks:
        device_info['disks'] = detected_disks
    if detected_shares:
        device_info['disk_shares'] = detected_shares
    detected_cpus = [
        {
            'family': 'QEMU Virtual',
            'model_name': 'QEMU Virtual CPU',
            'label': 'CPU {}'.format(i + 1),
            'index': i + 1,
            'cores': 1,
        } for i in range(cpu_count)
    ]
    if detected_cpus:
        device_info['processors'] = detected_cpus
    return device_info


def _get_virtual_machines(ssh, master_ip_address, hypervisor_ip_address):
    detected_machines = []
    storages = get_disk_shares(ssh)
    stdin, stdout, stderr = ssh.exec_command("qm list")
    for line in stdout:
        line = line.strip()
        if line.startswith('VMID'):
            continue
        vmid, name, status, mem, bootdisk, pid = (
            v.strip() for v in line.split()
        )
        if status != 'running':
            continue
        vmid = int(vmid)
        try:
            device_info = _get_virtual_machine_info(
                ssh,
                vmid,
                master_ip_address,
                storages,
                hypervisor_ip_address,
            )
        except NoLanError as e:
            logger.warning(unicode(e))
        else:
            detected_machines.append(device_info)
    return detected_machines


def _ssh_proxmox(ip_address, user, password):
    ssh = _connect_ssh(ip_address, user, password)
    try:
        cluster_cfg = None
        for command in (
            'cat /etc/pve/cluster.cfg',
            'cat /etc/pve/cluster.conf',
            'cat /etc/pve/storage.cfg',
            'pvecm help',
        ):
            stdin, stdout, stderr = ssh.exec_command(command)
            data = stdout.read()
            if data != '':
                if command == 'cat /etc/pve/cluster.cfg':
                    cluster_cfg = data
                break
        else:
            raise NoMatchError('This is not a PROXMOX server.')
        master_ip_address = _get_master_ip_address(
            ssh,
            ip_address,
            cluster_cfg,
        )
        cluster_member = _get_cluster_member(ssh, ip_address)
        subdevices = _get_virtual_machines(
            ssh,
            master_ip_address,
            ip_address,
        )
        if subdevices:
            cluster_member['subdevices'] = subdevices
    finally:
        ssh.close()
    return cluster_member


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_proxmox', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_USER and SSH_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            device_info = _ssh_proxmox(ip_address, user, password)
        except (ConnectionError, NoMatchError) as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result

