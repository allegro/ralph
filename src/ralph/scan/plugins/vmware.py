# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

from django.conf import settings
from lck.django.common.models import MACAddressField
from pysphere import VIServer, VIApiException

from ralph.discovery.models import DeviceType
from ralph.scan.errors import NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _get_vm_info(vm_properties, messages):
    if 'hostname' in vm_properties:
        hostname = vm_properties['hostname']
    else:
        hostname = vm_properties['name']
    ip_addresses = []
    mac_addresses = []
    for interface in vm_properties.get('net', []):
        if not interface['connected']:
            continue
        ip_v4 = []
        for ip in interface['ip_addresses']:
            if type(
                ipaddr.IPAddress(ip)
            ) == ipaddr.IPv4Address:
                ip_v4.append(ip)
        ip_addresses.extend(ip_v4)
        mac_addresses.append(
            MACAddressField.normalize(interface['mac_address'])
        )
    if not mac_addresses:
        messages.append(
            "Subdevice '{}' doesn't have any MAC addresses "
            "- removing it from scan results.".format(hostname)
        )
        return
    return {
        'type': DeviceType.virtual_server.raw,
        'model_name': 'VMWare Virtual Server',
        'mac_addresses': mac_addresses,
        'system_ip_addresses': ip_addresses,
        'hostname': hostname,
        'memory': [{
            'label': 'Virtual RAM',
            'size': vm_properties['memory_mb'],
        }],
        'processors': [
            {
                'family': 'Virtual CPU',
                'label': 'Virtual CPU %s' % i,
                'cores': 1,
                'index': i,
            } for i in xrange(0, vm_properties['num_cpu'])
        ],
        'disks': [
            {
                'label': disk['device']['label'],
                'size': int(disk['capacity'] / 1024),
                'family': 'VMWare Virtual Disk',
            } for disk in vm_properties.get('disks', [])
        ],
        'system_label': vm_properties['guest_full_name'],
    }


def _vmware(server_conn, ip_address, messages):
    subdevices = []
    for vm_path in server_conn.get_registered_vms():
        vm = server_conn.get_vm_by_path(vm_path)
        vm_properties = vm.get_properties()
        vm_info = _get_vm_info(vm_properties, messages)
        if vm_info:
            subdevices.append(vm_info)
    return {
        'type': DeviceType.unknown.raw,
        'system_ip_addresses': [ip_address],
        'subdevices': subdevices,
    }


def _connect(ip_address, user, password):
    server = VIServer()
    server.connect(ip_address, user, password)
    return server


def scan_address(ip_address, **kwargs):
    http_family = (kwargs.get('http_family', '') or '').strip().lower()
    snmp_name = (kwargs.get('snmp_name', '') or '').strip().lower()
    if all((
        'esx' not in http_family,
        'esx' not in snmp_name,
        'vmware' not in snmp_name,
    )):
        raise NoMatchError('It is not VMWare.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('vmware', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set VMWARE_USER and VMWARE_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            server_conn = _connect(ip_address, user, password)
        except VIApiException as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            try:
                if 'vcenter' in server_conn.get_server_type().lower():
                    raise NoMatchError(
                        "It is `VMware vCenter Server`. To save real "
                        "hypervisor - VM connecion you should scan only "
                        "VMware ESXi servers.",
                    )
                device_info = _vmware(server_conn, ip_address, messages)
            finally:
                server_conn.disconnect()
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
