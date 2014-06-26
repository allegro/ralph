#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based disco for IBM BladeCenters."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import time

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.util import network, parse
from ralph.discovery.models import (
    ComponentType,
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST,
)
from ralph.scan.plugins import get_base_result_template
from ralph.scan.errors import (
    TreeError, DeviceError, ConsoleError, NoMatchError, ConnectionError,
)


class Counts(object):

    def __init__(self):
        self.cpu = 0
        self.mem = 0
        self.blade = 0


class IBMSSHClient(paramiko.SSHClient):

    """SSHClient modified for IBM's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(IBMSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent,
              look_for_keys):
        """Do interactive auth if everything fails."""

        try:
            super(IBMSSHClient, self)._auth(
                username,
                password,
                pkey,
                key_filenames,
                allow_agent,
                look_for_keys,
            )
        except paramiko.BadAuthenticationType:
            self._transport.auth_interactive(
                username,
                lambda t, i, p: password,
            )
        self._ibm_chan = self._transport.open_session()
        self._ibm_chan.invoke_shell()
        self._ibm_chan.sendall('\r\n')
        time.sleep(0.125)
        chunk = self._ibm_chan.recv(1024)
        if not chunk.strip().startswith('system>'):
            raise ConsoleError('Expected a system prompt, got "%s".' % chunk)

    def ibm_command(self, command):
        """
        IBM's ssh has broken channel handling, so do everything in one
        big channel.
        """

        self._ibm_chan.sendall(command)
        buffer = ''
        while command not in buffer:
            buffer += self._ibm_chan.recv(1024)
        self._ibm_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._ibm_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if buffer[-1].startswith('system> '):
                return buffer[:-1]


def _connect_ssh(ip):
    return network.connect_ssh(
        ip,
        settings.SCAN_PLUGINS.get(__name__, {})['ssh_ibm_user'],
        settings.SCAN_PLUGINS.get(__name__, {})['ssh_ibm_password'],
        client=IBMSSHClient,
    )


def _component(model_type, pairs, parent, raw):
    model_type = ComponentType.unknown
    if 'Mach type/model' in pairs:
        model_name = '%s (%s)' % (pairs['Mach type/model'], pairs['Part no.'])
    elif 'Part no.' in pairs:
        model_name = pairs['Part no.']
    else:
        raise DeviceError('No model/part no.')
    if not model_name.startswith('IBM'):
        model_name = 'IBM ' + model_name
    sn = pairs.get('Mach serial number')
    if sn in SERIAL_BLACKLIST:
        sn = None
    if not sn:
        sn = pairs['FRU serial no.']
    if sn in SERIAL_BLACKLIST:
        sn = None
    if not sn:
        raise DeviceError('No serial no.')
    name = pairs.get('Name') or pairs.get('Product Name') or model_name
    if 'Management' in model_name:
        model_type = ComponentType.management
    elif 'Fibre Channel' in model_name:
        model_type = ComponentType.power
    elif 'Media' in model_name:
        model_type = ComponentType.media
    elif 'Cooling' in model_name:
        model_type = ComponentType.cooling
    elif 'Fan' in model_name:
        model_type = ComponentType.cooling
    elif 'Power Module' in model_name:
        model_type = ComponentType.power
    component = {}
    component['model_name'] = model_name
    component['serial_number'] = sn
    component['type'] = model_type.raw
    component['label'] = name
    firmware = (pairs.get('AMM firmware') or pairs.get('FW/BIOS') or
                pairs.get('Main Application 2'))
    if firmware:
        component['hard_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    else:
        if firmware:
            firmware = (
                pairs.get('Boot ROM') or pairs.get('Main Application 1') or
                pairs.get('Blade Sys Mgmt Processor')
            )
    if firmware:
        component['boot_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        component['mgmt_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Diagnostics'))
    if firmware:
        component['diag_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    if 'parts' not in parent:
        parent['parts'] = []
    parent['parts'].append(component)
    return parent


def _dev(model_type, pairs, parent, raw):
    device = {}
    if 'Mach type/model' in pairs:
        device['model_name'] = '%s (%s)' % (
            pairs['Mach type/model'],
            pairs['Part no.'],
        )
    elif 'Part no.' in pairs:
        device['model_name'] = pairs['Part no.']
    else:
        raise DeviceError('No model/part no.')
    if not device['model_name'].startswith('IBM'):
        device['model_name'] = 'IBM ' + device['model_name']
    sn = pairs.get('Mach serial number')
    if sn in SERIAL_BLACKLIST:
        sn = None
    if not sn:
        sn = pairs['FRU serial no.']
    if sn in SERIAL_BLACKLIST:
        sn = None
    device['serial_number'] = sn
    mac = pairs.get('MAC Address 1', None)
    if mac and mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST:
        device['mac_addresses'] = [MACAddressField.normalize(mac)]
    name = pairs.get('Name') or pairs.get(
        'Product Name') or device['model_name']
    device['name'] = name
    firmware = (pairs.get('AMM firmware') or pairs.get('FW/BIOS') or
                pairs.get('Main Application 2'))
    if firmware:
        device['hard_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    else:
        firmware = pairs.get('Power Module Cooling Device firmware rev.')
        if firmware:
            device['hard_firmware'] = 'rev %s' % firmware
    firmware = (pairs.get('Boot ROM') or pairs.get('Main Application 1') or
                pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        device['boot_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        device['mgmt_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Diagnostics'))
    if firmware:
        device['diag_firmware'] = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    return device


def _add_dev_mm(ip, pairs, parent, raw, counts, dev_id):
    parent['parts'] = [
        p for p in parent.get(
            'parts', []
        ) if p['type'] != ComponentType.management
    ]
    dev = _component(ComponentType.management, pairs, parent, raw)
    return dev


def _add_dev_generic(ip, pairs, parent, raw, counts, dev_id):
    if parent:
        return _component(ComponentType.unknown, pairs, parent, raw)
    else:
        dev = _dev(DeviceType.unknown, pairs, parent, raw)
        return dev


def _add_dev_cpu(ip, pairs, parent, raw, counts, dev_id):
    model = pairs.get('Mach type/model', 'unknown')
    counts.cpu += 1
    try:
        index = int(model.split()[-1])
    except ValueError:
        index = counts.cpu
    cpu = {
        'index': index,
        'label': pairs['Mach type/model'],
    }
    family = pairs['Processor family']
    if family.startswith('Intel '):
        family = cpu['label'][len('Intel '):]
    cpu['family'] = family
    speed = int(float(pairs['Speed'].replace('GHz', '')) * 1000)
    cores = int(pairs['Processor cores'])
    cpu.update({
        'model_name': model,
        'name': 'CPU %s %d MHz, %s-core' % (family, speed, cores),
        'speed': speed,
        'cores': cores,
    })
    if 'processors' not in parent:
        parent['processors'] = []
    parent['processors'].append(cpu)


def _add_dev_memory(ip, pairs, parent, raw, counts, dev_id):
    model = pairs.get('Mach type/model', 'unknown')
    counts.mem += 1
    try:
        index = int(model.split()[-1])
    except ValueError:
        index = counts.mem
    size = int(pairs['Size'].replace('GB', '')) * 1024
    speed = int(pairs.get('Speed', '0').replace('MHz', ''))
    label = pairs.get('Mach type/model', '')
    mem = dict(
        size=size,
        speed=speed,
        label=label,
        index=index,
    )
    if 'memory' not in parent:
        parent['memory'] = []
    parent['memory'].append(mem)


def _add_dev_blade(ip, pairs, parent, raw, counts, dev_id):
    if '[' in dev_id:
        pos = int(dev_id[dev_id.find('[') + 1:dev_id.find(']')])
    else:
        pos = None
    dev = _dev(DeviceType.blade_server, pairs, parent, raw)
    dev['chassis_position'] = pos
    counts.blade += 1
    for i in range(1, 9):
        name = 'MAC Address %d' % i
        mac = pairs.get(name)
        if mac == 'Not Available' or mac is None:
            continue
        if 'mac_addresses' not in dev:
            dev['mac_addresses'] = []
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST:
            dev['mac_addresses'].append(MACAddressField.normalize(mac))
    if 'mac_addresses' in dev:
        dev['mac_addresses'] = list(set(dev['mac_addresses']))
    return dev


def _add_dev_switch(ip, pairs, parent, raw, counts, dev_id):
    dev_type = DeviceType.switch
    if pairs['Mach type/model'].startswith('Fibre Channel SM'):
        dev_type = DeviceType.fibre_channel_switch
    dev = _dev(dev_type, pairs, parent, raw)
    mac = pairs.get('MAC Address')
    if mac:
        if 'mac_addresses' not in dev:
            dev['mac_addresses'] = []
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST:
            dev['mac_addresses'].append(MACAddressField.normalize(mac))
        dev['mac_addresses'] = list(set(dev['mac_addresses']))
    return dev


def _add_dev_system(ip, pairs, parent, raw, counts, dev_id):
    dev = _dev(DeviceType.blade_system, pairs, parent, raw)
    dev['management_ip_addresses'] = [ip]
    return dev


ADD_DEV = {
    'disk': _add_dev_generic,
    'exp': _add_dev_generic,
    'blower': _add_dev_generic,
    'power': _add_dev_generic,
    'mt': _add_dev_generic,
    'storage': _add_dev_generic,
    'cpu': _add_dev_cpu,
    'memory': _add_dev_memory,
    'mm': _add_dev_mm,
    'blade': _add_dev_blade,
    'system': _add_dev_system,
    'switch': _add_dev_switch,
}


def _prepare_devices(ssh, ip, dev_path, dev_id, components, parent=None,
                     counts=None,):
    if dev_path:
        full_path = '{}:{}'.format(dev_path, dev_id)
    else:
        full_path = dev_id
    if '[' in dev_id:
        dev_type = dev_id[0:dev_id.find('[')]
    else:
        dev_type = dev_id
    try:
        add_func = ADD_DEV[dev_type]
    except KeyError:
        return None
    lines = ssh.ibm_command('info -T {}'.format(full_path))
    raw = '\n'.join(lines)
    pairs = parse.pairs(lines=lines)
    try:
        dev = add_func(ip, pairs, parent, raw, counts, dev_id)
    except DeviceError:
        return
    for dev_info, components in components.iteritems():
        if counts is None:
            counts = Counts()
        dev_id = dev_info.split(None, 1)[0]
        subdev = _prepare_devices(
            ssh,
            ip,
            full_path,
            dev_id,
            components,
            dev,
            counts,
        )
        if subdev and subdev != dev:
            if 'subdevices' not in dev:
                dev['subdevices'] = []
            if subdev not in dev['subdevices']:
                dev['subdevices'].append(subdev)
    return dev


def _blade_scan(ip_address):
    ssh = _connect_ssh(ip_address)
    lines = ssh.ibm_command('list -l a')
    tree = parse.tree(lines=lines)
    if 'system' not in tree:
        raise TreeError('"system" not found in the device tree')
    device = _prepare_devices(ssh, ip_address, '', 'system', tree['system'])
    return device


def scan_address(ip_address, **kwargs):
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError('Incompatible Nexus found.')
    if kwargs.get('http_family', '') not in ('IBM', 'Unspecified'):
        raise NoMatchError('It is not IBM.')
    if not (kwargs.get('snmp_name', 'IBM') or 'IBM').startswith('IBM'):
        raise NoMatchError('It is not IBM.')
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on an IBM BladeServer.')
    messages = []
    result = get_base_result_template('ssh_ibm_bladecenter', messages)
    device = _blade_scan(ip_address)
    if not device:
        raise DeviceError("Malformed bladecenter device: %s" % ip_address)
    result['device'] = device
    result['status'] = 'success'
    return result
