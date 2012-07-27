#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko
import time

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network, plugin
from ralph.discovery.cisco import cisco_component, cisco_inventory
from ralph.discovery.models import DeviceType, Device, IPAddress


SSH_USER = settings.SSH_SSG_USER
SSH_PASSWORD = settings.SSH_SSG_PASSWORD


class Error(Exception):
    pass


class ConsoleError(Error):
    pass


class CiscoSSHClient(paramiko.SSHClient):
    """SSHClient modified for Cisco's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(CiscoSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent, look_for_keys):
        self._transport.auth_password(username, password)
        self._cisco_chan = self._transport.open_session()
        self._cisco_chan.invoke_shell()
        self._cisco_chan.sendall('\r\n')
        time.sleep(0.125)
        chunk = self._cisco_chan.recv(1024)
        if not chunk.endswith('#'):
            raise ConsoleError('Expected system prompt, got %r.' % chunk)

    def cisco_command(self, command):
        # XXX Work around random characters appearing at the beginning of the command.
        self._cisco_chan.sendall('\b')
        time.sleep(0.125)
        self._cisco_chan.sendall(command)
        buffer = ''
        end = command[-32:]
        while not buffer.strip('\b ').endswith(end):
            chunk = self._cisco_chan.recv(1024)
            buffer += chunk
        self._cisco_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._cisco_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if '% Invalid input' in buffer:
                raise ConsoleError('Invalid input %r.' % buffer)
            if buffer[-1].endswith('#'):
                return buffer[1:-1]

def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_USER, SSH_PASSWORD, client=CiscoSSHClient)


@nested_commit_on_success
def _run_ssh_catalyst(ip):
    ssh = _connect_ssh(ip)
    try:
        raw = '\n'.join(ssh.cisco_command("show inventory"))
    finally:
        ssh.close()

    inventory = list(cisco_inventory(raw))

    serials = [inv['sn'] for inv in inventory]

    try:
        dev = Device.objects.get(sn__in=serials)
    except Device.DoesNotExist:
        dev_inv = inventory[0]
        dev = Device.create(sn=dev_inv['sn'], model_name='Cisco %s' % dev_inv['pid'],
                model_type=DeviceType.switch,
                name=dev_inv['descr'][:255])
    dev.raw = raw
    dev.save(update_last_seen=True)

    for inv in inventory:
        cisco_component(dev, inv)

    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    if created:
        ip_address.hostname = network.hostname(ip_address.address)
    ip_address.device = dev
    ip_address.is_management = True
    ip_address.save(update_last_seen=True)
    return dev.name

@plugin.register(chain='discovery', requires=['ping', 'http', 'snmp'], priority=50)
def ssh_catalyst(**kwargs):
    if SSH_USER is None or SSH_PASSWORD is None:
        return False, 'no credentials.', kwargs
    ip = str(kwargs['ip'])
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    if kwargs.get('http_family') not in ('Unspecified', 'Cisco'):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = _run_ssh_catalyst(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs

