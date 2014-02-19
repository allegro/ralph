#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import socket
import time

from django.conf import settings

from ralph.discovery.cisco import cisco_component, cisco_inventory
from ralph.discovery.models import DeviceType
from ralph.scan.errors import (
    AuthError,
    ConnectionError,
    ConsoleError,
    NoMatchError,
    NotConfiguredError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
SSH_USER, SSH_PASSWORD = SETTINGS['ssh_user'], SETTINGS['ssh_pass']


if not SSH_USER or not SSH_PASSWORD:
    raise NotConfiguredError(
        "SSH not configured in plugin {}.".format(__name__),
    )


class CiscoSSHClient(paramiko.SSHClient):
    """SSHClient modified for Cisco's broken SSH console."""

    def __init__(self, *args, **kwargs):
        super(CiscoSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent, look_for_keys):
        self._transport.auth_password(username, password)
        self._cisco_chan = self._transport.open_session()
        self._cisco_chan.invoke_shell()
        self._cisco_chan.sendall('\r\n')
        self._cisco_chan.settimeout(15.0)
        time.sleep(4)
        try:
            chunk = self._cisco_chan.recv(1024)
        except socket.timeout:
            raise AuthError('Authentication failed.')
        else:
            if not chunk.endswith(('#', '>')):
                raise ConsoleError('Expected system prompt, got %r.' % chunk)

    def cisco_command(self, command):
        # XXX Work around random characters appearing at the beginning of the
        # command.
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
            if buffer[-1].endswith(('#', '>')):
                return buffer[1:-1]


def _connect_ssh(ip):
    if not network.check_tcp_port(ip, 22):
        raise ConnectionError('Port 22 closed.')
    return network.connect_ssh(
        ip, SSH_USER, SSH_PASSWORD, client=CiscoSSHClient,
    )


def get_subswitches(switch_version):
    pass


def scan_address(ip_address, **kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        raise NoMatchError('Incompatible Nexus found.')
    if kwargs.get('http_family') not in ('Unspecified', 'Cisco'):
        raise NoMatchError('It is not Cisco.')
    ssh = _connect_ssh(ip_address)
    try:
        mac = '\n'.join(ssh.cisco_command(
            "show version | include Base ethernet MAC Address",
        ))
        raw = '\n'.join(ssh.cisco_command("show inventory"))
    finally:
        ssh.close()
    mac = mac.strip()
    if mac.startswith("Base ethernet MAC Address") and ':' in mac:
        mac = mac.split(':', 1)[1].strip().replace(":", "")
    inventory = list(cisco_inventory(raw))
    dev_inv = inventory[0]
    model_name = 'Cisco Catalyst %s' % dev_inv['pid']
    sn = dev_inv['sn']
    model_type = DeviceType.switch
    parts = inventory[1:]
    result = get_base_result_template('ssh_cisco_catalyst')
    result.update({
        'status': 'success',
        'device': {
            'hostname': network.hostname(ip_address),
            'model_name': model_name,
            'type': unicode(model_type),
            'serial_number': sn,
            'mac_adresses': [mac],
            'management_ip_addresses': [ip_address],
            'parts': [{
                'serial_number': part['sn'],
                'name': part['name'],
                'label': part['descr'],
            } for part in parts],
        },
    })
    return result
