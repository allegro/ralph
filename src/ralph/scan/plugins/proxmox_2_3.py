# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging

from django.conf import settings
from lck.django.common.models import MACAddressField
import requests

from ralph.discovery.hardware import get_disk_shares
from ralph.discovery.models import DeviceType
from ralph.scan.errors import ConnectionError, NoMatchError, AuthError
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


logger = logging.getLogger("SCAN")


def _get_session(base_url, user, password):
    s = requests.Session()
    data = {'username': '{}@pam'.format(user), 'password': password}
    try:
        r = requests.post('{}/access/ticket'.format(base_url),
                          verify=False, data=data)
    except requests.ConnectionError:
        raise ConnectionError("Can't connect through API.")
    try:
        ticket = r.json()['data']['ticket']
    except (KeyError, TypeError):
        raise AuthError("Can't get access ticket through API.")
    s.headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
    }
    s.cookies = requests.cookies.cookiejar_from_dict({'PVEAuthCookie': ticket})
    s.verify = False
    return s


def _connect_ssh(ip_address, user, password):
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a Proxmox server.')
    return network.connect_ssh(ip_address, user, password)


def _get_node_name(ssh):
    stdin, stdout, stderr = ssh.exec_command("hostname")
    node_name = stdout.readline().split()[0]
    return node_name


def _get_node_sn(ssh):
    stdin, stdout, stderr = ssh.exec_command("sudo /usr/sbin/dmidecode -t 1 | grep -i serial")
    node_sn = stdout.readline().split()[-1]
    return node_sn


def _get_node_name_by_api(s, base_url, ip_address):
    # an alternative to '_get_node_name' which doesn't require ssh,
    # but is kind of slower and doesn't always work (e.g. with Proxmox3)
    url = '{}/cluster/status'.format(base_url)
    status = s.get(url).json()['data']
    node_name = None
    for i in status:
        if i.get('ip') == ip_address:
            node_name = i.get('name')
            break
    return node_name


def _get_proxmox_version(s, base_url):
    url = '{}/version'.format(base_url)
    _ = s.get(url).json()['data']
    version = '-'.join((_.get('version'), _.get('release')))
    return version


def _get_node_mac_address(ssh, iface='eth0'):
    command = "/sbin/ifconfig {} | head -n 1".format(iface)
    stdin, stdout, stderr = ssh.exec_command(command)
    mac = stdout.readline().split()[-1]
    mac = MACAddressField.normalize(mac)
    return mac


def _get_device_info(node_name, session, ssh, base_url):
    if session:
        url = '{}/nodes/{}/status'.format(base_url, node_name)
        cpuinfo = session.get(url).json()['data']['cpuinfo']
    elif ssh:
        stdin, stdout, stderr = ssh.exec_command(
            "sudo /usr/bin/pvesh get /nodes/{}/status".format(node_name)
        )
        data = stdout.read()
        cpuinfo = json.loads(data)['cpuinfo'] if data else None
    device_info = {}
    if cpuinfo:
        sockets = cpuinfo['sockets']
        cores = cpuinfo['cpus']
        processors = []
        for n in range(sockets):
            processors.append({
                # yes, differently than in VMs' case (cores divided by sockets)
                'cores': int(cores / sockets),
                'family': cpuinfo['model'],
                'speed': int(round(float(cpuinfo['mhz']))),
                'label': 'CPU {}'.format(n + 1),
            })
        device_info = {
            'model_name': 'Proxmox',
            'installed_software': [{
                'model_name': 'Proxmox',
                'path': 'proxmox',
            }],
            'processors': processors,
        }
    return device_info


def _get_vm_info(node_name, vmid, session, ssh, base_url, iface='net0'):
    if session:
        url = '{}/nodes/{}/qemu/{}/config'.format(base_url, node_name, vmid)
        vm_config = session.get(url).json()['data']
    elif ssh:
        stdin, stdout, stderr = ssh.exec_command(
            "sudo /usr/bin/pvesh get /nodes/{}/qemu/{}/config".format(node_name, vmid)
        )
        data = stdout.read()
        vm_config = json.loads(data) if data else None
    # get MACs
    mac_addresses = []
    net_raw = vm_config.get(iface)
    for i in net_raw.split(','):
        _ = i.split('=')
        if _[0] == 'virtio':
            mac_raw = _[1]
            mac_address = MACAddressField.normalize(mac_raw)
            if mac_address:
                mac_addresses.append(mac_address)
    # get CPUs
    processors = []
    sockets = vm_config.get('sockets')
    cores = vm_config.get('cores')
    for n in range(1, sockets + 1):
        processors.append({
            'cores': cores,
            'family': 'QEMU Virtual',
            'index': n,
            'label': 'CPU {}'.format(n),
            'model_name': 'QEMU Virtual CPU',
        })
    # get memory
    memory = [{
        'index': 0,
        'label': 'Virtual DIMM 0',
        'size': vm_config.get('memory'),
    }]
    # get HDDs
    disks = []
    for k, v in vm_config.iteritems():
        if k.startswith('virtio'):
            size, label = None, None
            for _ in v.split(','):
                if _.startswith('size'):
                    size = int(_.split('=')[-1][:-1]) * 1024  # GB -> MB
                elif _.startswith('vg'):
                    label = _.split(':')[-1]
            if label and size:
                disks.append({
                    'label': label,
                    'size': size,
                    'family': 'Proxmox Virtual Disk',
                    'model_name': 'Proxmox Virtual Disk {}MiB'.format(size),
                })
    vm_info = {
        'hostname': vm_config.get('name'),
        'mac_addresses': mac_addresses,
        'model_name': 'Proxmox qemu kvm',
        'processors': processors,
        'type': DeviceType.virtual_server.raw,
        'memory': memory,
        'disks': disks,
    }
    return vm_info


def _get_virtual_machines(node_name, session, ssh, base_url):
    if session:
        url = '{}/nodes/{}/qemu'.format(base_url, node_name)
        vms = session.get(url).json()['data']
    elif ssh:
        stdin, stdout, stderr = ssh.exec_command(
            "sudo /usr/bin/pvesh get /nodes/{}/qemu".format(node_name)
        )
        data = stdout.read()
        vms = json.loads(data) if data else []
    virtual_machines = []
    for vm in vms:
        vm = _get_vm_info(node_name, vm['vmid'], session, ssh, base_url)
        virtual_machines.append(vm)
    return virtual_machines


def _proxmox_2_3(ip_address, user, password):
    base_url = 'https://{}:{}/api2/json'.format(ip_address, 8006)
    try:
        session = _get_session(base_url, user, password)
    except (ConnectionError, AuthError):
        session = None
    ssh = _connect_ssh(ip_address, user, password)
    try:
        node_name = _get_node_name(ssh)
        node_sn = _get_node_sn(ssh)
        node_mac_address = _get_node_mac_address(ssh)
        disk_shares = get_disk_shares(ssh)
        # in a restricted environment a http session won't be available
        if not session:
            device_info = _get_device_info(node_name, session, ssh, base_url)
            vms = _get_virtual_machines(node_name, session, ssh, base_url)
    finally:
        ssh.close()
    if session:
        device_info = _get_device_info(node_name, session, ssh, base_url)
        vms = _get_virtual_machines(node_name, session, ssh, base_url)
    device_info.update({'system_ip_addresses': [ip_address]})
    if node_sn:
        device_info.update({'serial_number': node_sn})
    if node_mac_address:
        device_info.update({'mac_address': node_mac_address})
    if disk_shares:
        _ = []
        for lv, (wwn, size) in disk_shares.iteritems():
            _.append({
                'serial_number': wwn,
                'is_virtual': False,
                'size': size,
                'volume': lv,
            })
        device_info.update({'disk_shares': _})
    if vms:
        for vm in vms:
            vm['management'] = ip_address
        device_info['subdevices'] = vms
    return device_info


def scan_address(ip_address, **kwargs):
    if 'nx-os' in (kwargs.get('snmp_name') or '').lower():
        raise NoMatchError('Incompatible Nexus found.')
    if kwargs.get('http_family') not in ('Proxmox', 'Proxmox2', 'Proxmox3'):
        raise NoMatchError('It is not Proxmox 2 or 3.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('proxmox_2_3', messages)
    if not user or not password:
        result['status'] = 'error'
        msg = ('Not configured. Set SSH_USER and SSH_PASSWORD in your '
               'configuration file.')
        messages.append(msg)
    else:
        try:
            device_info = _proxmox_2_3(ip_address, user, password)
        except (ConnectionError, NoMatchError) as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({'status': 'success', 'device': device_info})
    return result
