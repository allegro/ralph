# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time

import paramiko

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.models import ComponentType, DeviceType, SERIAL_BLACKLIST
from ralph.scan.errors import ConnectionError, NoMatchError, SSHConsoleError
from ralph.scan.plugins import get_base_result_template
from ralph.util import parse
from ralph.util.network import check_tcp_port, connect_ssh


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class SSGSSHClient(paramiko.SSHClient):

    """SSHClient modified for SSG's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(SSGSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def old_command(self, command):
        stdin, stdout, stderr = self.exec_command(command)
        return stdout.realines()

    def _auth(self, username, password, pkey, key_filenames, allow_agent,
              look_for_keys):
        self._transport.auth_password(username, password)
        self._ssg_chan = self._transport.open_session()
        self._ssg_chan.invoke_shell()
        self._ssg_chan.sendall('\r\n')
        time.sleep(0.125)
        chunk = self._ssg_chan.recv(1024)
        if '->' not in chunk:
            raise SSHConsoleError('Expected system prompt, got "%s".' % chunk)

    def ssg_command(self, command):
        """
        IBM's ssh has broken channel handling, so do everything in one
        big channel.
        """

        self._ssg_chan.sendall(command)
        buffer = ''
        while not buffer.endswith(command):
            buffer += self._ssg_chan.recv(1024)
        self._ssg_chan.sendall('\r\n')
        buffer = ['']
        while True:
            chunk = self._ssg_chan.recv(1024)
            lines = chunk.split('\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if '->' in buffer[-1]:
                return buffer[:-1]
            if chunk.endswith('--- more --- '):
                self._ssg_chan.sendall('\n')


def _connect_ssh(ip_address, user, password):
    if not check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed.')
    return connect_ssh(ip_address, user, password, client=SSGSSHClient)


def _ssh_ssg(ip_address, user, password):
    ssh = _connect_ssh(ip_address, user, password)
    lines = ssh.ssg_command('get system')
    pairs = parse.pairs(lines=lines[:10])
    name = pairs['Product Name']
    version = pairs['Hardware Version'].split(',', 1)[0]
    model = '%s %s' % (name, version)
    mac = pairs['Base Mac'].replace('.', '').upper()
    sn = pairs['Serial Number'].split(',', 1)[0]
    result = {
        'type': DeviceType.firewall.raw,
        'model_name': model,
        'mac_addresses': [MACAddressField.normalize(mac)],
        'hostname': name,
        'management_ip_addresses': [ip_address],
        'parts': [{
            'boot_firmware': pairs['Software Version'].split(',', 1)[0],
            'type': ComponentType.power.raw,
        }],
    }
    if sn not in SERIAL_BLACKLIST:
        result['serial_number'] = sn
    return result


def scan_address(ip_address, **kwargs):
    if kwargs.get('http_family') not in ('SSG', 'Unspecified'):
        raise NoMatchError("It's not a Juniper SSG.")
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError("Incompatible Nexus found.")
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_ssg', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_SSG_USER and SSH_SSG_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            device_info = _ssh_ssg(ip_address, user, password)
        except ConnectionError as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
