#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based disco for IBM BladeCenters."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
import socket

from django.conf import settings
from lck.django.common import nested_commit_on_success
import paramiko
from lck.django.common.models import MACAddressField

from ralph.util import network, parse, plugin, Eth
from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    Device,
    DeviceType,
    Ethernet,
    GenericComponent,
    IPAddress,
    Memory,
    Processor,
    SERIAL_BLACKLIST,
)
from ralph.discovery.models_history import DiscoveryWarning


SAVE_PRIORITY = 50


class Error(Exception):
    pass


class TreeError(Error):
    pass


class ConsoleError(Error):
    pass


class DeviceError(Error):
    pass


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
        settings.SSH_IBM_USER,
        settings.SSH_IBM_PASSWORD,
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
        # FIXME: merge GenericComponent(model__type=fibre) and FibreChannel
        model_type = ComponentType.fibre
        return None
    elif 'Power' in model_name:
        model_type = ComponentType.power
    elif 'Media' in model_name:
        model_type = ComponentType.media
    elif 'Cooling' in model_name:
        model_type = ComponentType.cooling
    elif 'Fan' in model_name:
        model_type = ComponentType.cooling
    model, mcreated = ComponentModel.create(
        model_type,
        family=model_name,
        name=model_name,
        priority=SAVE_PRIORITY,
    )
    component, created = GenericComponent.concurrent_get_or_create(
        sn=sn,
        defaults=dict(
            device=parent,
        ),
    )
    component.model = model
    component.label = name
    firmware = (pairs.get('AMM firmware') or pairs.get('FW/BIOS') or
                pairs.get('Main Application 2'))
    if firmware:
        component.hard_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    else:
        firmware = pairs.get('Power Module Cooling Device firmware rev.')
        if firmware:
            component.hard_firmware = 'rev %s' % firmware
    firmware = (pairs.get('Boot ROM') or pairs.get('Main Application 1') or
                pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        component.boot_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        component.mgmt_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Diagnostics'))
    if firmware:
        component.diag_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    component.save(update_last_seen=True, priority=SAVE_PRIORITY)
    return component


def _dev(model_type, pairs, parent, raw):
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
    mac = pairs.get('MAC Address 1', None)
    if mac:
        ethernets = [Eth('MAC Address 1', mac, None)]
    else:
        ethernets = []
    name = pairs.get('Name') or pairs.get('Product Name') or model_name
    dev = Device.create(
        ethernets=ethernets,
        model_name=model_name,
        model_type=model_type,
        sn=sn,
        name=name,
        parent=parent,
        priority=SAVE_PRIORITY,
    )
    firmware = (pairs.get('AMM firmware') or pairs.get('FW/BIOS') or
                pairs.get('Main Application 2'))
    if firmware:
        dev.hard_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    else:
        firmware = pairs.get('Power Module Cooling Device firmware rev.')
        if firmware:
            dev.hard_firmware = 'rev %s' % firmware
    firmware = (pairs.get('Boot ROM') or pairs.get('Main Application 1') or
                pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        dev.boot_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Blade Sys Mgmt Processor'))
    if firmware:
        dev.mgmt_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    firmware = (pairs.get('Diagnostics'))
    if firmware:
        dev.diag_firmware = '%s %s rev %s' % (
            firmware['Build ID'],
            firmware['Rel date'],
            firmware['Rev'],
        )
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
    return dev


def _add_dev_mm(ip, pairs, parent, raw, counts, dev_id):
    _component(ComponentType.management, pairs, parent, raw)

    # XXX Clean up the previously added components
    for child in parent.child_set.filter(
        model__type__in=[DeviceType.management, DeviceType.unknown],
    ):
        child.delete()


def _add_dev_generic(ip, pairs, parent, raw, counts, dev_id):
    if parent:
        _component(ComponentType.unknown, pairs, parent, raw)
    else:
        dev = _dev(DeviceType.unknown, pairs, parent, raw)
        return dev


def _add_dev_cpu(ip, pairs, parent, raw, counts, dev_id):
    try:
        model = pairs['Mach type/model']
    except KeyError:
        DiscoveryWarning(
            message="Processor model unknown",
            plugin=__name__,
            device=parent,
            ip=ip,
        ).save()
        return
    counts.cpu += 1
    try:
        index = int(model.split()[-1])
    except ValueError:
        index = counts.cpu
    cpu, created = Processor.concurrent_get_or_create(
        device=parent,
        index=index,
    )
    cpu.label = pairs['Mach type/model']
    family = pairs['Processor family']
    if family.startswith('Intel '):
        family = cpu.label[len('Intel '):]
    speed = int(float(pairs['Speed'].replace('GHz', '')) * 1000)
    cores = int(pairs['Processor cores'])
    cpu.model, c = ComponentModel.create(
        ComponentType.processor,
        speed=speed,
        cores=cores,
        name='CPU %s %d MHz, %s-core' % (family, speed, cores),
        family=family,
        priority=SAVE_PRIORITY,
    )
    cpu.save(priority=SAVE_PRIORITY)


def _add_dev_memory(ip, pairs, parent, raw, counts, dev_id):
    try:
        model = pairs['Mach type/model']
    except KeyError:
        DiscoveryWarning(
            message="Memory model unknown",
            plugin=__name__,
            device=parent,
            ip=ip,
        ).save()
        return
    counts.mem += 1
    try:
        index = int(model.split()[-1])
    except ValueError:
        index = counts.mem
    mem, created = Memory.concurrent_get_or_create(device=parent, index=index)
    size = int(pairs['Size'].replace('GB', '')) * 1024
    speed = int(pairs.get('Speed', '0').replace('MHz', ''))
    mem.label = pairs.get('Mach type/model', '')
    mem.model, c = ComponentModel.create(
        ComponentType.memory,
        size=size,
        speed=speed,
        priority=SAVE_PRIORITY,
    )
    mem.save(priority=SAVE_PRIORITY)


def _add_dev_blade(ip, pairs, parent, raw, counts, dev_id):
    if '[' in dev_id:
        pos = int(dev_id[dev_id.find('[') + 1:dev_id.find(']')])
    else:
        pos = None
    dev = _dev(DeviceType.blade_server, pairs, parent, raw)
    dev.chassis_position = pos
    if pos:
        dev.position = '%02d' % pos
    else:
        dev.position = ''
    counts.blade += 1
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
    for i in range(1, 9):
        name = 'MAC Address %d' % i
        mac = pairs.get(name)
        if mac == 'Not Available' or mac is None:
            continue
        eth, created = Ethernet.concurrent_get_or_create(
            mac=MACAddressField.normalize(mac),
            defaults=dict(device=dev),
        )
        eth.label = name
        eth.save(priority=SAVE_PRIORITY)
    return dev


def _add_dev_switch(ip, pairs, parent, raw, counts, dev_id):
    dev_type = DeviceType.switch
    if pairs['Mach type/model'].startswith('Fibre Channel SM'):
        dev_type = DeviceType.fibre_channel_switch
    dev = _dev(dev_type, pairs, parent, raw)
    mac = pairs.get('MAC Address')
    if mac:
        eth, created = Ethernet.concurrent_get_or_create(
            mac=MACAddressField.normalize(mac),
            defaults=dict(device=dev),
        )
        eth.label = 'Ethernet'
        eth.save(priority=SAVE_PRIORITY)
    return dev


def _add_dev_system(ip, pairs, parent, raw, counts, dev_id):
    dev = _dev(DeviceType.blade_system, pairs, parent, raw)
    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    if created:
        ip_address.hostname = network.hostname(ip_address.address)
    ip_address.device = dev
    ip_address.is_management = True   # FIXME: how do we know for sure?
    ip_address.save(update_last_seen=True)   # no priorities for IP addresses
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


def _recursive_add_dev(ssh, ip, dev_path, dev_id, components, parent=None,
                       counts=None):
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
        pass
    else:
        for dev_info, components in components.iteritems():
            if counts is None:
                counts = Counts()
            dev_id = dev_info.split(None, 1)[0]
            _recursive_add_dev(
                ssh,
                ip,
                full_path,
                dev_id,
                components,
                dev,
                counts,
            )
        return dev


@nested_commit_on_success
def run_ssh_bladecenter(ip):
    ssh = _connect_ssh(ip)
    lines = ssh.ibm_command('list -l a')
    tree = parse.tree(lines=lines)
    if 'system' not in tree:
        raise TreeError('"system" not found in the device tree')
    dev = _recursive_add_dev(ssh, ip, '', 'system', tree['system'])
    return dev.name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_ibm_bladecenter(**kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family', '') not in ('IBM', 'Unspecified'):
        return False, 'no match.', kwargs
    if not kwargs.get('snmp_name', 'IBM').startswith('IBM'):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        DiscoveryWarning(
            message="Port 22 closed on an IBM BladeServer.",
            plugin=__name__,
            ip=ip,
        ).save()
        return False, 'closed.', kwargs
    try:
        name = run_ssh_bladecenter(ip)
    except (network.Error, Error, paramiko.SSHException, socket.error) as e:
        DiscoveryWarning(
            message="This is an IBM BladeServer, but: " + str(e),
            plugin=__name__,
            ip=ip,
        ).save()
        return False, str(e), kwargs
    return True, name, kwargs


def ssh_ibm_reboot(ip, bay):
    ssh = _connect_ssh(ip)
    command = "power -cycle -T system:blade[%s]" % bay
    result = ssh.ibm_command(command)
    return len(result) > 1 and result[1] and result[1].strip().lower() == 'ok'
