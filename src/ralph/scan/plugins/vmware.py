# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from pysphere import VIServer, VIApiException

from ralph.discovery.models import DeviceType
from ralph.scan.errors import NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _get_vm_info(vm_properties):
    ip_addresses = []
    mac_addresses = []
    for interface in vm_properties.get('net', []):
        if not interface['connected']:
            continue
        ip_addresses.extend(interface['ip_addresses'])
        mac_addresses.append(interface['mac_address'])
    return {
        'type': DeviceType.virtual_server.raw,
        'mac_addresses': mac_addresses,
        'system_ip_addresses': ip_addresses,
        'hostname': vm_properties['hostname'],
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
            } for disk in vm_properties.get('disks', [])
        ],
        'system_label': vm_properties['guest_full_name'],
    }


def _vmware(server_conn, ip_address):
    subdevices = []
    for vm_path in server_conn.get_registered_vms():
        vm = server_conn.get_vm_by_path(vm_path)
        vm_properties = vm.get_properties()
        subdevices.append(_get_vm_info(vm_properties))
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
    http_family = kwargs.get('http_family', '').strip()
    if http_family and http_family.lower() not in ('esx',):
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
                device_info = _vmware(server_conn, ip_address)
            finally:
                server_conn.disconnect()
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
