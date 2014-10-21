# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings
from lck.django.common.models import MACAddressField
import requests

# from ralph.discovery.hardware import get_disk_shares
from ralph.discovery.models import DeviceType
from ralph.scan.errors import ConnectionError, NoMatchError
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


logger = logging.getLogger("SCAN")

def _get_session(base_url, user, password):
    s = requests.Session()
    ticket = None
    data = {'username': user + '@pam', 'password': password}
    r = requests.post(base_url + '/access/ticket', verify=False, data=data)
    if r.status_code == 200:
        ticket = r.json()['data']['ticket']
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
    stdin, stdout, stderr = ssh.exec_command("dmidecode -t 1 | grep -i serial")
    node_sn = stdout.readline().split()[-1]
    return node_sn


def _get_node_name_by_api(s, base_url, ip_address):
    # an alternative to '_get_node_name' which doesn't require ssh,
    # but is kind of slower and doesn't always work (e.g. with Proxmox3)
    url = base_url + '/cluster/status'
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
    command = "ifconfig " + iface + " | head -n 1"
    stdin, stdout, stderr = ssh.exec_command(command)
    mac = stdout.readline().split()[-1]
    mac = MACAddressField.normalize(mac)
    return mac


def _get_device_info(s, base_url, node_name):
    url = '{}/nodes/{}/status'.format(base_url, node_name)
    cpuinfo = s.get(url).json()['data']['cpuinfo']
    sockets = cpuinfo['sockets']
    cores = cpuinfo['cpus']
    processors = []
    for n in range(sockets):
        processors.append({
            'cores': int(cores / sockets),  # yes, differently than in VMs' case
            'family': cpuinfo['model'],
            'speed': int(round(float(cpuinfo['mhz']))),
            'label': 'CPU ' + str(n + 1),
        })
    di = {
        'model_name': 'Proxmox',
        'installed_software': [{'model_name': 'Proxmox', 'path': 'proxmox'}],
        'processors': processors,
    }
    return di


def _get_virtual_machine_info(s, base_url, node_name, vmid, iface='net0'):
    url = '{}/nodes/{}/qemu/{}/config'.format(base_url, node_name, vmid)
    vm_config = s.get(url).json()['data']
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
            'label': 'CPU ' + str(n),
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
                disks.append({'label': label, 'size': size})
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


def _get_virtual_machines(s, base_url, node_name):
    url = '{}/nodes/{}/qemu'.format(base_url, node_name)
    vms = s.get(url).json()['data']
    virtual_machines = []
    for vm in vms:
        vm = _get_virtual_machine_info(s, base_url, node_name, vm['vmid'])
        virtual_machines.append(vm)
    return virtual_machines


def _proxmox_2_3(ip_address, user, password):
    base_url = 'https://{}:{}/api2/json'.format(ip_address, 8006)
    s = _get_session(base_url, user, password)
    ssh = _connect_ssh(ip_address, user, password)
    try:
        node_name = _get_node_name(ssh)
        node_sn = _get_node_sn(ssh)
        node_mac_address = _get_node_mac_address(ssh)
        # storages = get_disk_shares(ssh)
    finally:
        ssh.close()
    device_info = _get_device_info(s, base_url, node_name)
    device_info.update({'system_ip_addresses': [ip_address]})
    if node_sn:
        device_info.update({'serial_number': node_sn})
    if node_mac_address:
        device_info.update({'mac_address': node_mac_address})
    virtual_machines = _get_virtual_machines(s, base_url, node_name)
    if virtual_machines:
        for vm in virtual_machines:
            vm['management'] = ip_address
        device_info['subdevices'] = virtual_machines
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
        messages.append(
            'Not configured. Set SSH_USER and SSH_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            device_info = _proxmox_2_3(ip_address, user, password)
        except (ConnectionError, NoMatchError) as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
