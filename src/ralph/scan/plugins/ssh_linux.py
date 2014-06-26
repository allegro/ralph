# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.hardware import get_disk_shares
from ralph.discovery.models import SERIAL_BLACKLIST
from ralph.discovery.models_component import is_mac_valid
from ralph.scan.plugins import get_base_result_template
from ralph.util import network, parse, Eth
from ralph.scan.errors import NoMatchError


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _parse_dmidecode(data):
    """Parse data returned by the dmidecode command into a dict."""

    parsed_data = parse.multi_pairs(data)

    if 'System Information' not in parsed_data:
        return {}
    result = {
        'model_name': parsed_data['System Information']['Product Name'],
    }
    serial_number = parsed_data['System Information']['Serial Number']
    if 'not specified' not in serial_number.lower():
        if serial_number not in SERIAL_BLACKLIST:
            result['serial_number'] = serial_number

    def exclude(value, exceptions):
        if value not in exceptions:
            return value

    def num(value):
        if value is None or value.lower() == 'unknown':
            return None
        try:
            num, unit = value.split(None, 1)
        except ValueError:
            num = value
        return int(num)

    processors = []
    for cpu in parsed_data.getlist('Processor Information'):
        if not cpu:
            continue
        processor = {
            'label': cpu['Socket Designation'],
            'family': cpu['Family'],
        }
        speed = num(cpu['Current Speed'])
        if speed:
            processor['speed'] = speed
        cores = num(cpu.get('Core Count'))
        if cores:
            processor['cores'] = cores
        if 'not specified' not in cpu['Version'].lower():
            processor['model_name'] = cpu['Version']
        processors.append(processor)
    if processors:
        result['processors'] = processors
    memory = []
    for mem in parsed_data.getlist('Memory Device'):
        if any((
            not mem,
            mem and mem.get('Size') == 'No Module Installed',
        )):
            continue
        memory_chip = {
            'label': mem['Locator'],
        }
        size = num(mem['Size'])
        if size:
            memory_chip['size'] = size
        speed = num(exclude(mem.get('Speed'), {'Unknown'}))
        if speed:
            memory_chip['speed'] = speed
        memory.append(memory_chip)
    if memory:
        result['memory'] = memory
    return result


def _get_mac_addresses(ssh):
    """Get the MAC addresses"""

    stdin, stdout, stderr = ssh.exec_command(
        "/sbin/ip addr show | /bin/grep 'link/ether'",
    )
    mac_addresses = set()
    for line in stdout:
        mac_address = line.split(None, 3)[1]
        if is_mac_valid(Eth(label='', mac=mac_address, speed=0)):
            mac_addresses.add(MACAddressField.normalize(mac_address))
    return list(mac_addresses)


def _get_base_device_info(ssh, messages=[]):
    """Handle dmidecode data"""

    stdin, stdout, stderr = ssh.exec_command(
        "/usr/bin/sudo /usr/sbin/dmidecode",
    )
    device_info = _parse_dmidecode(stdout.read())
    if not device_info:
        messages.append('DMIDECODE: System information not found.')
    return device_info


def _get_hostname(ssh):
    stdin, stdout, stderr = ssh.exec_command("/bin/hostname -f")
    return stdout.read().strip()


def _get_os_visible_memory(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        "/bin/grep 'MemTotal:' '/proc/meminfo'",
    )
    label, memory, unit = stdout.read().strip().split(None, 2)
    return int(int(memory) / 1024)


def _get_os_visible_storage(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        "/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM "
        "| /bin/grep '^/'"
    )
    total = 0
    for line in stdout:
        path, size, rest = line.split(None, 2)
        total += int(size.replace('M', ''))
    return total


def _get_os_visible_cores_count(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        "/bin/grep '^processor' '/proc/cpuinfo'",
    )
    return len(stdout.readlines())


def _get_os_info(ssh):
    stdin, stdout, stderr = ssh.exec_command("/bin/uname -a")
    family, host, version, release, rest = stdout.read().strip().split(None, 4)
    return {
        'system_label': '%s %s' % (release, version),
        'system_family': family,
        'system_memory': _get_os_visible_memory(ssh),
        'system_storage': _get_os_visible_storage(ssh),
        'system_cores_count': _get_os_visible_cores_count(ssh),
    }


def _get_disk_shares(ssh):
    return [
        {
            'serial_number': wwn,
            'size': size,
            'volume': lv,
        } for lv, (wwn, size) in get_disk_shares(ssh).iteritems()
    ]


def _ssh_linux(ssh, ip_address, messages=[]):
    device_info = _get_base_device_info(ssh)
    mac_addresses = _get_mac_addresses(ssh)
    if mac_addresses:
        device_info['mac_addresses'] = mac_addresses
    device_info['system_ip_addresses'] = [ip_address]
    device_info['hostname'] = _get_hostname(ssh)
    disk_shares = _get_disk_shares(ssh)
    if disk_shares:
        device_info['disk_shares'] = disk_shares
    device_info.update(_get_os_info(ssh))
    return device_info


def scan_address(ip_address, **kwargs):
    messages = []
    result = get_base_result_template('ssh_linux', messages)
    snmp_name = kwargs.get('snmp_name', '') or ''
    if not snmp_name:
        raise NoMatchError("No snmp found")
    snmp_name = snmp_name.lower()
    if 'nx-os' in snmp_name:
        messages.append('Incompatible Nexus found.')
        result['status'] = 'error'
        return result
    if all((
        'linux' not in snmp_name,
        'xen' not in snmp_name,
        not snmp_name.startswith('vmware esx'),
    )):
        messages.append('No match.')
        result['status'] = 'error'
        return result
    ssh = None
    auths = SETTINGS.get('auths', [])
    for user, password in auths:
        if user is None or password is None:
            continue
        try:
            ssh = network.connect_ssh(ip_address, user, password)
        except network.AuthError:
            continue
        else:
            break
    if not ssh:
        messages.append('Authorization failed')
        result['status'] = 'error'
        return result
    try:
        device_info = _ssh_linux(ssh, ip_address)
    except (network.Error, paramiko.SSHException) as e:
        messages.append(unicode(e))
        result['status'] = 'error'
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result
