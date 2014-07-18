#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based scan for Cisco ASA firewalls."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import re
import socket
import time

from django.conf import settings

from ralph.discovery import guessmodel
from ralph.discovery.models import (
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST
)
from ralph.scan.errors import (
    AuthError,
    ConsoleError,
    NoMatchError,
    NotConfiguredError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util import parse, network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
SSH_USER, SSH_PASS = SETTINGS['ssh_user'], SETTINGS['ssh_pass']


class CiscoSSHClient(paramiko.SSHClient):

    """SSHClient modified for Cisco's broken SSH console."""

    def __init__(self, *args, **kwargs):
        super(CiscoSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(
        self, username, password, pkey, key_filenames, allow_agent,
        look_for_keys,
    ):
        self._transport.auth_password(username, password)
        self._asa_chan = self._transport.open_session()
        self._asa_chan.invoke_shell()
        self._asa_chan.sendall('\r\n')
        self._asa_chan.settimeout(15.0)
        time.sleep(0.125)
        try:
            chunk = self._asa_chan.recv(1024)
        except socket.timeout:
            raise AuthError('Authentication failed.')
        else:
            if '> ' not in chunk and not chunk.strip().startswith('asa'):
                raise ConsoleError('Expected system prompt, got %r.' % chunk)

    def asa_command(self, command):
        # XXX Work around random characters
        # appearing at the beginning of the command.
        self._asa_chan.sendall('\b')
        time.sleep(0.125)
        self._asa_chan.sendall(command)
        buffer = ''
        while not command.endswith(
            buffer[max(0, buffer.rfind('\b')):][:len(command)].strip('\b'),
        ):
            chunk = self._asa_chan.recv(1024)
            buffer += chunk.replace('\b', '')
        self._asa_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._asa_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if '% Invalid input' in buffer:
                raise ConsoleError('Invalid input %r.' % buffer)
            if '> ' in buffer[-1]:
                return buffer[1:-1]


def _connect_ssh(ip, username='root', password=''):
    return network.connect_ssh(ip, username, password, client=CiscoSSHClient)


def scan_address(ip_address, **kwargs):
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError('Incompatible Nexus found.')
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gvendor != 'Cisco' or gmodel not in ('',):
        raise NoMatchError('It is not Cisco.')
    if not SSH_USER or not SSH_PASS:
        raise NotConfiguredError(
            "SSH not configured in plugin {}.".format(__name__),
        )
    ssh = _connect_ssh(ip_address, SSH_USER, SSH_PASS)
    try:
        lines = ssh.asa_command(
            "show version | grep (^Hardware|Boot microcode|^Serial|address is)"
        )
    finally:
        ssh.close()
    pairs = parse.pairs(lines=[line.strip() for line in lines])
    sn = pairs.get('Serial Number', None)
    model, ram, cpu = pairs['Hardware'].split(',')
    boot_firmware = pairs['Boot microcode']
    macs = []
    for i in xrange(99):
        try:
            junk, label, mac = pairs['%d' % i].split(':')
        except KeyError:
            break
        mac = mac.split(',', 1)[0]
        mac = mac.replace('address is', '')
        mac = mac.replace('.', '').upper().strip()
        label = label.strip()
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST:
            macs.append(mac)
    ram_size = re.search('[0-9]+', ram).group()
    cpu_match = re.search('[0-9]+ MHz', cpu)
    cpu_speed = cpu_match.group()[:-4]
    cpu_model = cpu[:cpu_match.start()][4:].strip()
    result = get_base_result_template('ssh_cisco_asa')
    result.update({
        'status': 'success',
        'device': {
            'model_name': 'Cisco ' + model,
            'type': str(DeviceType.firewall),
            'mac_addresses': macs,
            'boot_firmware': boot_firmware,
            'management_ip_addresses': [ip_address],
            'memory': [{
                'size': int(ram_size),
            }],
            'processors': [{
                'model_name': cpu_model,
                'speed': int(cpu_speed),
                'family': cpu_model,
            }],
        },
    })
    if sn not in SERIAL_BLACKLIST:
        result['device']['serial_number'] = sn
    return result
