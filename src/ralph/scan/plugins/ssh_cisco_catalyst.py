#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import time

from django.conf import settings

from ralph.util import network
from ralph.discovery.models import DeviceType
from ralph.discovery.cisco import cisco_component, cisco_inventory
from ralph.scan.plugins import get_base_result_template


class NotConfiguredError(Exception):
    pass


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
SSH_USER, SSH_PASSWORD = SETTINGS['ssh_user'], SETTINGS['ssh_pass']

if not SSH_USER or not SSH_PASSWORD:
    raise NotConfiguredError(
        "ssh not configured in plugin {}".format(__name__),
    )


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
        time.sleep(4)
        chunk = self._cisco_chan.recv(1024)
        if not chunk.endswith(('#', '>')):
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
            if buffer[-1].endswith(('#', '>')):
                return buffer[1:-1]


def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_USER, SSH_PASSWORD, client=CiscoSSHClient)


def scan_address(ip_address, **kwargs):
    status = 'success'
    ssh = _connect_ssh(ip_address)
    try:
        mac = '\n'.join(ssh.cisco_command(
            "show version | include Base ethernet MAC Address"
        ))
        raw = '\n'.join(ssh.cisco_command("show inventory"))
    finally:
        ssh.close()

    mac = mac.strip()
    if mac.startswith("Base ethernet MAC Address") and ':' in mac:
        mac = mac.split(':', 1)[1].strip().replace(":", "")
    else:
        ethernets = None
    inventory = list(cisco_inventory(raw))
    serials = [inv['sn'] for inv in inventory]
    dev_inv = inventory[0]
    model_name='Cisco Catalyst %s' % dev_inv['pid']
    sn = dev_inv['sn']
    model_type=DeviceType.switch
    device = {
              'hostname': network.hostname(ip_address),
              'model_name': model_name,
              'type': str(model_type),
              'serial_number': sn,
              'mac_adresses': [mac, ],
              'management_ip_addresses': [ip_address, ],
    }
    parts = inventory[1:]
    device['parts'] = []
    for p in parts:
        part = {
                'serial_number': p['sn'],
                'name': p['name'],
                'label': p['descr'],
        }
        device['parts'].append(part)
    ret = {
        'status': status,
        'device': device,
    }
    tpl = get_base_result_template('ssh_cisco_catalyst')
    tpl.update(ret)
    return tpl